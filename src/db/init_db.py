from motor.motor_asyncio import AsyncIOMotorClient
import logging
from src.db.connection import settings

logger = logging.getLogger(__name__)

async def init_db():
    """Initialize database with indexes and initial setup."""
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]

        # Create indexes for users collection
        await db.users.create_index("email", unique=True)
        await db.users.create_index("created_at")

        # Create indexes for events collection
        await db.events.create_index([
            ("user_id", 1),
            ("provider", 1),
            ("provider_event_id", 1)
        ], unique=True)
        await db.events.create_index([
            ("user_id", 1),
            ("start", 1),
            ("end", 1)
        ])

        # Create indexes for sessions collection
        await db.sessions.create_index([
            ("user_id", 1),
            ("provider", 1),
            ("expires_at", 1)
        ])
        await db.sessions.create_index("expires_at", expireAfterSeconds=0)

        # Create indexes for agent_logs collection
        await db.agent_logs.create_index([
            ("user_id", 1),
            ("created_at", -1)
        ])

        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        client.close() 