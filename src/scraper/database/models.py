"""
SQLAlchemy models for content storage
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CachedContent(Base):
    """Model representing cached content from URLs"""
    __tablename__ = 'cached_content'

    # URL is the primary key, normalized to ensure uniqueness
    url = Column(String(2048), primary_key=True)

    # The actual content fetched from the URL
    content = Column(Text, nullable=False)

    # Timestamps for tracking
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CachedContent(url='{self.url}', fetched_at='{self.fetched_at}')>"

    def to_dict(self):
        """Convert the model instance to a dictionary"""
        return {
            'url': self.url,
            'content': self.content,
            'fetched_at': self.fetched_at,
            'updated_at': self.updated_at
        }
