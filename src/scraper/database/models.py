"""
SQLAlchemy models for content storage
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Index, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CachedContent(Base):
    """Model representing cached content from URLs"""
    __tablename__ = 'cached_content'

    # Independent primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # URL with an index for efficient lookups
    url = Column(String(2048), nullable=False, unique=True, index=True)

    # The actual content fetched from the URL
    content = Column(Text, nullable=False)

    # Timestamps for tracking
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    fetched_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # Create an explicit index on the URL column
    __table_args__ = (
        Index('idx_cached_content_url', 'url'),
    )

    def __repr__(self):
        return f"<CachedContent(id={self.id}, url='{self.url}', fetched_at='{self.fetched_at}')>"

    def to_dict(self):
        """Convert the model instance to a dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'content': self.content,
            'fetched_at': self.fetched_at,
            'updated_at': self.updated_at,
            'created_at': self.created_at
        }

class Property(Base):
    """Model representing a property"""
    __tablename__ = 'property'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rightmove_id = Column(String(255), nullable=False, unique=True, index=True)
    data = Column(JSON, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    fetched_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_rightmove_id', 'rightmove_id'),
    )

    def __repr__(self):
        return f"<Property(id={self.id}, rightmove_id={self.rightmove_id}, fetched_at='{self.fetched_at}')>"

    def to_dict(self):
        """Convert the model instance to a dictionary"""
        return {
            'id': self.id,
            'rightmove_id': self.rightmove_id,
            'data': self.data,
            'fetched_at': self.fetched_at,
            'updated_at': self.updated_at,
            'created_at': self.created_at
        }
