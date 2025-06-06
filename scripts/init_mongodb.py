#!/usr/bin/env python3
"""
Initialize MongoDB with sample data for development and testing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from src.db.connection import MongoDB
from src.models.mongodb_models import User, Event, Session, AgentLog
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use environment variables for tokens
SAMPLE_SESSION_TOKEN = os.getenv("SAMPLE_SESSION_TOKEN", "sample_session_token")
SAMPLE_REFRESH_TOKEN = os.getenv("SAMPLE_REFRESH_TOKEN", "sample_session_refresh")

async def create_sample_data():
    """Create sample data in MongoDB."""
    try:
        # Connect to MongoDB
        db = MongoDB()
        await db.connect()
        
        # Create sample user
        user = User(
            email="test@example.com",
            google_token={
                "access_token": "sample_access_token",
                "refresh_token": "sample_refresh_token",
                "expires_at": datetime.utcnow() + timedelta(hours=1)
            }
        )
        created_user = await db.users.insert_one(user.dict())
        user_id = created_user.inserted_id
        logger.info(f"Created sample user with ID: {user_id}")
        
        # Create sample events
        events = [
            Event(
                user_id=user_id,
                provider="google",
                provider_event_id=f"event_{i}",
                summary=f"Sample Event {i}",
                start=datetime.utcnow() + timedelta(hours=i),
                end=datetime.utcnow() + timedelta(hours=i+1)
            ) for i in range(3)
        ]
        for event in events:
            await db.events.insert_one(event.dict())
        logger.info("Created sample events")
        
        # Create sample session
        session = Session(
            user_id=user_id,
            provider="google",
            access_token=SAMPLE_SESSION_TOKEN,
            refresh_token=SAMPLE_REFRESH_TOKEN,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        await db.sessions.insert_one(session.dict())
        logger.info("Created sample session")
        
        # Create sample agent logs
        logs = [
            AgentLog(
                user_id=user_id,
                intent="list_events",
                input_text="Show me my calendar",
                steps=[{"step": 1, "action": "list_events"}],
                final_output="Found 3 events"
            ),
            AgentLog(
                user_id=user_id,
                intent="create_event",
                input_text="Schedule a meeting tomorrow",
                steps=[{"step": 1, "action": "create_event"}],
                final_output="Created event: Team Meeting"
            )
        ]
        for log in logs:
            await db.agent_logs.insert_one(log.dict())
        logger.info("Created sample agent logs")
        
        logger.info("Sample data initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing sample data: {e}")
        raise
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_sample_data()) 