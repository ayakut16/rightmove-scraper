"""
Fetcher class providing a layer on top of HTTP client with caching capabilities
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from .http_client import HttpClient
from .database.base import Database
from .database.sqlite import SQLiteDatabase
from .utils.url import normalize_url


class Fetcher:
    """
    A fetcher class that provides cached HTTP content retrieval.

    This class:
    1. Normalizes URLs for consistent caching
    2. Checks if content is already in the database and recent enough
    3. Fetches from the network only when necessary
    4. Stores new content in the database
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        http_client: Optional[HttpClient] = None,
        cache_ttl_hours: float = 6.0,
        db_path: str = 'content_cache.db'
    ):
        """
        Initialize the fetcher.

        Args:
            db: An instance of Database. If None, a SQLiteDatabase will be created.
            http_client: An instance of HttpClient. If None, a new one will be created.
            cache_ttl_hours: Time-to-live for cached content in hours.
            db_path: Path to the SQLite database file if a new db is created.
        """
        # Create or use the provided database
        self.db = db if db is not None else SQLiteDatabase(db_path)
        self.db.initialize()

        # Create or use the provided HTTP client
        self.http_client = http_client if http_client is not None else HttpClient()

        # Set cache TTL
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

    def fetch(self, url: str, force_refresh: bool = False, **kwargs) -> Optional[str]:
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
        from_cache = False

        if not force_refresh:
            # Check cache first
            cached_data = self.db.get_content(normalized_url)
            if cached_data:
                fetched_at = cached_data['fetched_at']
                now = datetime.utcnow()

                # If cache is fresh enough, use it
                if now - fetched_at < self.cache_ttl:
                    content = cached_data['content']
                    from_cache = True
                    print(f"Using cached content for {url} (cached {now - fetched_at} ago)")

        # If not using cache, fetch from network
        if content is None:
            print(f"Fetching content from network for {url}")
            content = self.http_client.get(normalized_url, **kwargs)

            # If fetch was successful, save to cache
            if content:
                self.db.save_content(normalized_url, content)

        return content

    def close(self):
        """Close database connections and perform cleanup"""
        self.db.close()

    def __enter__(self):
        """Support for context manager usage"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure database is closed when context manager exits"""
        self.close()
