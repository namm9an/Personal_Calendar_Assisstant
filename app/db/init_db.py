"""
Database initialization module.
"""
import logging
try:
    from app.db.dev_db import mongodb
except ImportError:
    from app.db.mongodb import mongodb

logger = logging.getLogger(__name__)

async def init_db():
    """Initialize database with indexes and initial setup."""
    try:
        # Check if we're using the development database
        if hasattr(mongodb, 'db_path'):
            # For development database, we don't need to create indexes
            logger.info("Using development database, skipping index creation")
            return
            
        # For MongoDB, create indexes
        # Create indexes for users collection
        await mongodb.db.users.create_index("email", unique=True)
        await mongodb.db.users.create_index("created_at")

        # Create indexes for events collection
        await mongodb.db.events.create_index([
            ("user_id", 1),
            ("provider", 1),
            ("provider_event_id", 1)
        ], unique=True)
        await mongodb.db.events.create_index([
            ("user_id", 1),
            ("start", 1),
            ("end", 1)
        ])

        # Create indexes for sessions collection
        await mongodb.db.sessions.create_index([
            ("user_id", 1),
            ("provider", 1),
            ("expires_at", 1)
        ])
        await mongodb.db.sessions.create_index("expires_at", expireAfterSeconds=0)

        # Create indexes for agent_logs collection
        await mongodb.db.agent_logs.create_index([
            ("user_id", 1),
            ("created_at", -1)
        ])

        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise 