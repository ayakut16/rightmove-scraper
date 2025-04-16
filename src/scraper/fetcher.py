"""
Fetcher class providing a layer on top of HTTP client with caching capabilities
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union

from scraper.http_client import HttpClient
from .database.base import Database
from .database.sqlite import SQLiteDatabase
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

    def __init__(self, db: Optional[Database] = None, cache_ttl_hours: float = 6.0):
        """
        Initialize the fetcher.

        Args:
            db: An instance of Database. If None, a SQLiteDatabase will be created.
            cache_ttl_hours: Time-to-live for cached content in hours.
        """
        # Create or use the provided database
        self.db = db if db is not None else SQLiteDatabase()
        self.db.initialize()

        # Create or use the provided HTTP client
        self.http_client = HttpClient()

        # Set cache TTL
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

        # Create or use the provided parser
        self.parser = PropertyPageParser()

    async def fetch_sitemap(self, url: str, force_refresh: bool = False, **kwargs) -> Optional[str]:
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
            content = await self.http_client.get(normalized_url, **kwargs)

            # If fetch was successful, save to cache
            if content:
                self.db.save_content(normalized_url, content)

        return content

    async def fetch_property(self, url: str, force_refresh: bool = False, **kwargs) -> Optional[str]:
        """
        Fetch content from a URL, using cache if available and recent.
        """
        # fetch the numbers after /properties/ with regex
        normalized_url = normalize_url(url)
        property_id = re.search(r'/properties/(\d+)', url).group(1)
        property = None

        if not force_refresh:
            # Check cache first
            saved_property = self.db.get_property(property_id)
            if saved_property:
                fetched_at = saved_property['fetched_at']
                # Make fetched_at timezone-aware if it isn't already
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)

                # If cache is fresh enough, use it
                if now - fetched_at < self.cache_ttl:
                    property = saved_property['data']

        if property is None:
            property_html = await self.http_client.get(normalized_url, **kwargs)
            property_data = self.parser.parse(property_html)
            self.db.save_property(property_id, property_data)

        return property

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
