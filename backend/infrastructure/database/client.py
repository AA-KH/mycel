"""
Centralized Database Client for Mycel.
Re-exports the existing MongoDB connection for use within the infrastructure domain.
"""

from core.mongodb import mongodb_connection
from core.logger import logger

async def get_db():
    """Dependency injection provider for the database instance."""
    try:
        return mongodb_connection.db
    except RuntimeError as e:
        logger.error(f"Database provider error: {str(e)}")
        raise
