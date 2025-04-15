"""
Abstract base class for content database implementations using SQLAlchemy
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from .models import Base, CachedContent


class ContentDatabase(ABC):
    """
    Abstract base class defining the interface for content caching and storage.
    Uses SQLAlchemy for database operations.
    """

    def __init__(self):
        """Initialize the database connection"""
        self.engine = None
        self.session_factory = None
        self._session = None

    def _create_engine(self) -> None:
        self.engine = create_engine(f"sqlite:///{self.db_path}")

    def initialize(self) -> None:
        """Create tables if they don't exist"""
        # Make sure engine is created
        if self.engine is None:
            self._create_engine()

        # Create tables
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a SQLAlchemy session"""
        # Make sure engine is created
        if self.engine is None:
            self._create_engine()

        # Create session factory if needed
        if self.session_factory is None:
            self.session_factory = sessionmaker(bind=self.engine)

        # Create session if needed
        if self._session is None:
            self._session = self.session_factory()

        return self._session

    def get_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve content for a given URL from the database.

        Args:
            url: The normalized URL to fetch content for

        Returns:
            A dictionary containing 'content' and 'fetched_at' or None if not found
        """
        session = self.get_session()
        cached = session.query(CachedContent).filter_by(url=url).first()
        if cached:
            return cached.to_dict()
        return None

    def save_content(self, url: str, content: str) -> None:
        """
        Save or update content for a URL in the database.

        Args:
            url: The normalized URL to save content for
            content: The content to save
        """
        session = self.get_session()

        # Try to find existing record
        cached = session.query(CachedContent).filter_by(url=url).first()

        if cached:
            # Update existing record
            cached.content = content
            cached.fetched_at = datetime.utcnow()
        else:
            # Create new record
            cached = CachedContent(url=url, content=content)
            session.add(cached)

        session.commit()

    def get_last_fetched_time(self, url: str) -> Optional[datetime]:
        """
        Get the timestamp when URL was last fetched.

        Args:
            url: The normalized URL to check

        Returns:
            Datetime of last fetch or None if URL has never been fetched
        """
        session = self.get_session()
        cached = session.query(CachedContent).filter_by(url=url).first()
        return cached.fetched_at if cached else None

    def close(self) -> None:
        """
        Close the database connection and perform any cleanup.
        """
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        """Support for context manager usage"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure database is closed when context manager exits"""
        self.close()
