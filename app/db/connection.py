"""Database connection module for MongoDB."""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class DBConnection:
    client: AsyncIOMotorClient = None

db = DBConnection()

async def connect_to_mongo():
    """Connect to MongoDB."""
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)

async def close_mongo_connection():
    """Close MongoDB connection."""
    db.client.close()

async def get_db():
    """Get MongoDB database instance."""
    if db.client is None:
        await connect_to_mongo()
    return db.client[settings.MONGODB_DB_NAME] 