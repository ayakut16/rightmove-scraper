"""
Fetcher class providing a layer on top of HTTP client with caching capabilities
"""

import asyncio
import os
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union, List
import dotenv

from scraper.http_client import HttpClient
from .database.sqlite import SQLiteDatabase
from .database.postgres import PostgresDatabase
from .utils.url import normalize_url
from .parser import PropertyPageParser

class Fetcher:
    """
    A fetcher class that provides cached HTTP content retrieval.

    This class:
    1. Normalizes URLs for consistent caching
    2. Checks if content is already in the database and recent enough
    3. Fetches from the network only when necessary
    4. Stores new content in the database
    """

    def __init__(self, cache_ttl_hours: float = 6.0):
        """
        Initialize the fetcher.

        Args:
            db: An instance of Database. If None, a SQLiteDatabase will be created.
            cache_ttl_hours: Time-to-live for cached content in hours.
        """
        dotenv.load_dotenv()
        postgres_url = os.getenv('POSTGRES_URL')
        # Create or use the provided database
        self.db = PostgresDatabase(postgres_url) if postgres_url else SQLiteDatabase()
        self.db.initialize()

        # Create or use the provided HTTP client
        self.http_client = HttpClient()

        # Set cache TTL
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

        # Create or use the provided parser
        self.parser = PropertyPageParser()

    def get_existing_property_rightmove_ids(self):
        return self.db.get_all_property_rightmove_ids()

    def get_expired_property_rightmove_ids(self, hours: int = 6):
        return self.db.get_expired_property_rightmove_ids(hours)

    async def fetch_webpage(self, url: str, force_refresh: bool = False, **kwargs) -> Optional[str]:
        """
        Fetch content from a URL, using cache if available and recent.

        Args:
            url: The URL to fetch
            force_refresh: If True, ignore cache and always fetch from network
            **kwargs: Additional arguments to pass to the HTTP client's get method

        Returns:
            The content as a string, or None if the fetch failed
        """
        # Normalize the URL for consistent caching
        normalized_url = normalize_url(url)
        # Check if we need to fetch or can use cache
        content = None

        if not force_refresh:
            # Check cache first
            cached_data = self.db.get_content(normalized_url)

            if cached_data:
                fetched_at = cached_data['fetched_at']
                # Make fetched_at timezone-aware if it isn't already
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)

                # If cache is fresh enough, use it
                if now - fetched_at < self.cache_ttl:
                    content = cached_data['content']
        # If not using cache, fetch from network
        if content is None:
            # Properly await the async get method
            content, _ = await self.http_client.get(normalized_url, **kwargs)

            # If fetch was successful, save to cache
            if content:
                self.db.save_content(normalized_url, content)

        return content

    async def fetch_and_save_properties(self, rightmove_ids: List[int], **kwargs) -> Dict[str, Any]:
        """
        Fetch multiple properties, using cache if available and recent.
        Only fetches from network for properties that are not in cache or are expired.

        Args:
            urls: List of property URLs to fetch
            **kwargs: Additional arguments to pass to the HTTP client's get method

        Returns:
            Dictionary mapping property IDs to their data
        """

        urls_to_fetch = [f"https://www.rightmove.co.uk/properties/{rightmove_id}" for rightmove_id in rightmove_ids]
        url_to_rightmove_id = dict(zip(urls_to_fetch, rightmove_ids))
        # Fetch missing or expired properties
        async def fetch_single_property(url: str) -> tuple[str, Optional[dict]]:
            rightmove_id = url_to_rightmove_id[url]
            try:
                property_html, status_code = await self.http_client.get(url, **kwargs)
                if status_code == 404 or status_code == 410:
                    return rightmove_id, None
                property_data = self.parser.parse(property_html)
                return rightmove_id, property_data
            except Exception as e:
                # print(f"Error fetching property {rightmove_id}: {str(e)}")
                return None, None

        # Fetch all properties in parallel and collect results
        fetch_results = await asyncio.gather(
            *(fetch_single_property(url) for url in urls_to_fetch)
        )

        # Update result dictionary and collect properties to save
        result = {}
        properties_to_save = []
        for rightmove_id, property_data in fetch_results:
            if rightmove_id:
                result[rightmove_id] = property_data
                properties_to_save.append({
                    'rightmove_id': rightmove_id,
                    'data': property_data
                })

        # Batch save all fetched properties
        if properties_to_save:
            self.db.save_properties(properties_to_save)

        return result

    async def close(self):
        """Close database connections and perform cleanup"""
        self.db.close()
        await self.http_client.close()

    async def __aenter__(self):
        """Support for async context manager usage"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure database is closed when async context manager exits"""
        await self.close()

    # For backwards compatibility with non-async code
    def __enter__(self):
        """Support for synchronous context manager usage (not recommended)"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure database is closed when synchronous context manager exits"""
        asyncio.run(self.close())
