"""
SQLite implementation of the content database using SQLAlchemy
"""

import os
from sqlalchemy import create_engine

from .base import ContentDatabase


class SQLiteContentDatabase(ContentDatabase):
    """SQLite implementation of the content database"""

    def __init__(self, db_path: str = 'content_cache.db'):
        """
        Initialize the SQLite database.

        Args:
            db_path: Path to the SQLite database file. Defaults to 'content_cache.db'
                     in the current working directory.
        """
        super().__init__()
        # Create directory for the database if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.connection_string = f"sqlite:///{db_path}"
