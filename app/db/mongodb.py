"""
MongoDB connection module using Motor.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_to_database(cls):
        """Create database connection."""
        try:
            settings = get_settings()
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
            cls.db = cls.client[settings.MONGODB_DB]
            # Verify connection
            await cls.client.admin.command('ping')
            logger.info("Connected to MongoDB!")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    @classmethod
    async def close_database_connection(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection!")

# Create global instance
mongodb = MongoDB() 