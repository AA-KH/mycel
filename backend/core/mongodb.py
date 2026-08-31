"""
MongoDB Database Connection.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from core.logger import logger

class MongoDBConnection:
    client: AsyncIOMotorClient = None

    async def connect(self):
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        try:
            client = AsyncIOMotorClient(settings.mongodb_url)
            # Verify connection
            await client.admin.command('ping')
            self.client = client
            logger.info("Successfully connected to MongoDB")
        except Exception as error:
            self.client = None
            raise error

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    @property
    def db(self):
        if self.client:
            return self.client.get_database(settings.mongodb_database)
        raise RuntimeError("MongoDB client is not initialized")

mongodb_connection = MongoDBConnection()
