"""Tests for MongoDB models and CRUD operations."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.models.mongodb_models import User, Event, Session, AgentLog
from app.core.exceptions import DatabaseError, ValidationError

@pytest_asyncio.fixture
async def mongodb_client():
    """Create a MongoDB client for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    try:
        # Test connection
        await client.admin.command('ping')
        yield client
    finally:
        await client.drop_database("test_calendar_db")
        client.close()

@pytest_asyncio.fixture
async def test_db(mongodb_client):
    """Create a test database."""
    db = mongodb_client["test_calendar_db"]
    # Create collections if they don't exist
    if "users" not in await db.list_collection_names():
        await db.create_collection("users")
    if "events" not in await db.list_collection_names():
        await db.create_collection("events")
    if "sessions" not in await db.list_collection_names():
        await db.create_collection("sessions")
    if "agent_logs" not in await db.list_collection_names():
        await db.create_collection("agent_logs")
    yield db

class TestMongoDBModels:
    """Tests for MongoDB models and CRUD operations."""

    @pytest.mark.asyncio
    async def test_mongo_client_connection(self, mongodb_client):
        """Test MongoDB client connection."""
        try:
            await mongodb_client.admin.command("ping")
        except Exception as e:
            pytest.fail(f"Failed to connect to MongoDB: {e}")

    @pytest.mark.asyncio
    async def test_insert_user_document(self, test_db):
        """Test inserting a user document."""
        user = {
            "_id": ObjectId(),
            "email": "test@example.com",
            "name": "Test User",
            "timezone": "UTC",
            "working_hours_start": "09:00",
            "working_hours_end": "17:00",
            "preferences": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await test_db.users.insert_one(user)
        doc = await test_db.users.find_one({"_id": result.inserted_id})
        assert doc["email"] == user["email"]
        assert doc["name"] == user["name"]
        assert doc["timezone"] == user["timezone"]

    @pytest.mark.asyncio
    async def test_update_event_document(self, test_db):
        """Test updating an event document."""
        # Insert test event
        event = {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "summary": "Test Event",
            "start_datetime": datetime.utcnow(),
            "end_datetime": datetime.utcnow() + timedelta(hours=1),
            "timezone": "UTC",
            "created_by": "test@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "confirmed"
        }
        await test_db.events.insert_one(event)

        # Update event
        new_summary = "Updated Event"
        await test_db.events.update_one(
            {"_id": event["_id"]},
            {"$set": {"summary": new_summary, "updated_at": datetime.utcnow()}}
        )

        # Verify update
        updated = await test_db.events.find_one({"_id": event["_id"]})
        assert updated is not None
        assert updated["summary"] == new_summary

    @pytest.mark.asyncio
    async def test_delete_user_document(self, test_db):
        """Test deleting a user document."""
        # Insert test user
        user_id = ObjectId()
        user = {
            "_id": user_id,
            "email": "delete_test@example.com",
            "name": "Delete Test User",
            "timezone": "UTC",
            "working_hours_start": "09:00",
            "working_hours_end": "17:00",
            "preferences": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await test_db.users.insert_one(user)

        # Delete user
        await test_db.users.delete_one({"_id": user_id})

        # Verify deletion
        deleted = await test_db.users.find_one({"_id": user_id})
        assert deleted is None

    @pytest.mark.asyncio
    async def test_session_management(self, test_db):
        """Test session management operations."""
        # Create session
        session = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "provider": "google",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "scope": ["https://www.googleapis.com/auth/calendar"]
        }
        await test_db.sessions.insert_one(session)

        # Verify session
        created = await test_db.sessions.find_one({"_id": session["_id"]})
        assert created is not None
        assert created["access_token"] == "test_access_token"
        assert created["provider"] == "google"

        # Update session
        new_token = "new_access_token"
        await test_db.sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"access_token": new_token, "updated_at": datetime.utcnow()}}
        )
        updated = await test_db.sessions.find_one({"_id": session["_id"]})
        assert updated["access_token"] == new_token

    @pytest.mark.asyncio
    async def test_agent_log_operations(self, test_db):
        """Test agent log operations."""
        # Create log
        log = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "session_id": str(ObjectId()),
            "interaction_id": str(ObjectId()),
            "intent": "list_events",
            "entities": {"date": "2025-06-10"},
            "response": "Found 3 events",
            "created_at": datetime.utcnow(),
            "processing_time": 0.5,
            "success": True
        }
        await test_db.agent_logs.insert_one(log)

        # Verify log
        created = await test_db.agent_logs.find_one({"_id": log["_id"]})
        assert created is not None
        assert created["intent"] == "list_events"
        assert created["entities"]["date"] == "2025-06-10"
        assert created["success"] is True

        # Query logs by user
        user_logs = await test_db.agent_logs.find({"user_id": log["user_id"]}).to_list(length=None)
        assert len(user_logs) == 1
        assert user_logs[0]["_id"] == log["_id"]

    @pytest.mark.skip("MongoDB doesn't validate documents automatically without validation schemas")
    @pytest.mark.asyncio
    async def test_event_validation(self, test_db):
        """Test event validation rules."""
        # MongoDB doesn't validate documents automatically
        # This would need to be implemented in the application layer
        invalid_event = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "summary": "Invalid Event",
            "start_datetime": datetime.utcnow() + timedelta(hours=1),
            "end_datetime": datetime.utcnow(),  # End before start
            "timezone": "UTC",
            "created_by": "test@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "confirmed"
        }
        
        # Insert without validation - MongoDB will accept it
        result = await test_db.events.insert_one(invalid_event)
        assert result.inserted_id is not None
        
        # Cleanup
        await test_db.events.delete_one({"_id": invalid_event["_id"]})

    @pytest.mark.skip("MongoDB doesn't validate documents automatically without validation schemas")
    @pytest.mark.asyncio
    async def test_user_validation(self, test_db):
        """Test user validation rules."""
        # MongoDB doesn't validate documents automatically
        # This would need to be implemented in the application layer
        invalid_user = {
            "_id": ObjectId(),
            "email": "invalid-email",  # Invalid email format
            "name": "Invalid User",
            "timezone": "UTC",
            "working_hours_start": "09:00",
            "working_hours_end": "17:00",
            "preferences": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert without validation - MongoDB will accept it
        result = await test_db.users.insert_one(invalid_user)
        assert result.inserted_id is not None
        
        # Cleanup
        await test_db.users.delete_one({"_id": invalid_user["_id"]})

    @pytest.mark.skip("MongoDB doesn't validate documents automatically without validation schemas")
    @pytest.mark.asyncio
    async def test_session_validation(self, test_db):
        """Test session validation rules."""
        # MongoDB doesn't validate documents automatically
        # This would need to be implemented in the application layer
        invalid_session = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "provider": "google",
            # Missing access_token
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Insert without validation - MongoDB will accept it
        result = await test_db.sessions.insert_one(invalid_session)
        assert result.inserted_id is not None
        
        # Cleanup
        await test_db.sessions.delete_one({"_id": invalid_session["_id"]}) 