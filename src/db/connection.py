from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "calendar_db"

    class Config:
        env_file = ".env"

settings = Settings()

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect_to_database(cls):
        """Create database connection."""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
            cls.db = cls.client[settings.MONGODB_DB_NAME]
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