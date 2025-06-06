from motor.motor_asyncio import AsyncIOMotorClient
import logging
from src.db.connection import settings
from datetime import datetime
from src.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

async def init_db():
    """Initialize database with indexes and validation."""
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]

        # Create indexes for users collection
        await db.users.create_index("email", unique=True)
        await db.users.create_index("google_id", sparse=True)
        await db.users.create_index("microsoft_id", sparse=True)
        await db.users.create_index("created_at")

        # Create indexes for events collection
        await db.events.create_index([("user_id", 1), ("start", 1)])
        await db.events.create_index([("user_id", 1), ("end", 1)])
        await db.events.create_index("provider_event_id", sparse=True)
        await db.events.create_index("recurring_event_id", sparse=True)
        await db.events.create_index("created_at")

        # Create indexes for sessions collection
        await db.sessions.create_index("user_id")
        await db.sessions.create_index("token", unique=True)
        await db.sessions.create_index("expires_at", expireAfterSeconds=0)
        await db.sessions.create_index([("user_id", 1), ("provider", 1)])

        # Create indexes for agent_logs collection
        await db.agent_logs.create_index("user_id")
        await db.agent_logs.create_index("created_at")
        await db.agent_logs.create_index([("user_id", 1), ("action", 1)])

        # Create collection validation
        await _create_collection_validation(db)

        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Database initialization failed: {str(e)}")
    finally:
        client.close()

async def _create_collection_validation(db):
    """Create collection validation rules."""
    try:
        # Users collection validation
        await db.command({
            "collMod": "users",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["email", "timezone", "created_at", "updated_at"],
                    "properties": {
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                        },
                        "timezone": {
                            "bsonType": "string"
                        },
                        "working_hours_start": {
                            "bsonType": "string",
                            "pattern": "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
                        },
                        "working_hours_end": {
                            "bsonType": "string",
                            "pattern": "^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
                        }
                    }
                }
            }
        })
        
        # Events collection validation
        await db.command({
            "collMod": "events",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "summary", "start", "end", "provider"],
                    "properties": {
                        "user_id": {
                            "bsonType": "string"
                        },
                        "summary": {
                            "bsonType": "string",
                            "minLength": 1
                        },
                        "start": {
                            "bsonType": "date"
                        },
                        "end": {
                            "bsonType": "date"
                        },
                        "provider": {
                            "enum": ["google", "microsoft"]
                        }
                    }
                }
            }
        })
        
        # Sessions collection validation
        await db.command({
            "collMod": "sessions",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "token", "expires_at", "provider"],
                    "properties": {
                        "user_id": {
                            "bsonType": "string"
                        },
                        "token": {
                            "bsonType": "string",
                            "minLength": 1
                        },
                        "expires_at": {
                            "bsonType": "date"
                        },
                        "provider": {
                            "enum": ["google", "microsoft"]
                        }
                    }
                }
            }
        })
        
        # Agent logs collection validation
        await db.command({
            "collMod": "agent_logs",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "action", "input_text", "status"],
                    "properties": {
                        "user_id": {
                            "bsonType": "string"
                        },
                        "action": {
                            "bsonType": "string",
                            "minLength": 1
                        },
                        "input_text": {
                            "bsonType": "string",
                            "minLength": 1
                        },
                        "status": {
                            "enum": ["success", "error", "in_progress"]
                        }
                    }
                }
            }
        })
        
        logger.info("Collection validation rules created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create collection validation: {e}")
        raise DatabaseError(f"Collection validation creation failed: {str(e)}") 