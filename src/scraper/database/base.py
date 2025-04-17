"""
Abstract base class for content database implementations using SQLAlchemy
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from .models import Base, CachedContent, Property


class Database(ABC):
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
        self.engine = create_engine(self.connection_string)

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

    def get_all_property_rightmove_ids(self) -> List[int]:
        """
        Retrieve all property Rightmove IDs from the database.
        Uses a targeted query to fetch only IDs for better performance.
        """
        session = self.get_session()
        # Each row is a tuple with one element: (rightmove_id,)
        rows = session.query(Property.rightmove_id).all()
        # Extract the first element from each tuple
        return [row[0] for row in rows]

    def get_property(self, rightmove_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve property for a given Rightmove ID from the database.
        """
        session = self.get_session()
        property = session.query(Property).filter_by(rightmove_id=rightmove_id).first()
        return property.to_dict() if property else None

    def get_properties(self, rightmove_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve properties for a given list of Rightmove IDs from the database. Returns None for IDs not present.
        """
        session = self.get_session()
        properties = session.query(Property).filter(Property.rightmove_id.in_(rightmove_ids)).all()
        result = {rightmove_id: None for rightmove_id in rightmove_ids}
        for property in properties:
            result[property.rightmove_id] = property.to_dict()
        return result

    def save_properties(self, properties: List[Dict[str, Any]]) -> None:
        """
        Bulk save or update properties for a given list of Rightmove IDs in the database.
        Uses SQLAlchemy's bulk operations for better performance.
        """
        session = self.get_session()

        # Get existing properties
        rightmove_ids = [p['rightmove_id'] for p in properties]
        existing_properties = {
            p.rightmove_id: p for p in
            session.query(Property).filter(Property.rightmove_id.in_(rightmove_ids))
        }

        # Prepare bulk updates and inserts
        now = datetime.now(timezone.utc)
        to_update = []
        to_insert = []

        for property_data in properties:
            rightmove_id = property_data['rightmove_id']
            if rightmove_id in existing_properties:
                existing = existing_properties[rightmove_id]
                existing.data = property_data['data']
                existing.fetched_at = now
                to_update.append(existing)
            else:
                to_insert.append(Property(
                    rightmove_id=rightmove_id,
                    data=property_data['data'],
                    fetched_at=now
                ))

        if to_insert:
            session.bulk_save_objects(to_insert)
        session.commit()

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
            cached.fetched_at = datetime.now(timezone.utc)
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
