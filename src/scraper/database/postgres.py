"""
PostgreSQL implementation of the content database using SQLAlchemy
"""

from sqlalchemy import create_engine

from .base import ContentDatabase


class PostgresContentDatabase(ContentDatabase):
    """PostgreSQL implementation of the content database"""

    def __init__(self, connection_string: str):
        """
        Initialize the PostgreSQL database.

        Args:
            connection_string: Connection string for PostgreSQL,
                              e.g. 'postgresql://username:password@localhost/dbname'
        """
        super().__init__()
        self.connection_string = connection_string

    def _create_engine(self) -> None:
        """Create the SQLAlchemy engine for PostgreSQL"""
        self.engine = create_engine(self.connection_string)
