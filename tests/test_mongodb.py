"""Tests for MongoDB integration."""
import pytest
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.exceptions import DatabaseError, ValidationError
from app.models.mongodb_models import User, Event, Session, AgentLog

class TestMongoDBModels:
    """Tests for MongoDB models."""

    @pytest.fixture
    def test_user_data(self):
        """Create test user data."""
        return {
            "email": "test@example.com",
            "name": "Test User",
            "timezone": "UTC",
            "working_hours": {
                "start": "09:00",
                "end": "17:00",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            },
            "preferences": {
                "notification_enabled": True,
                "notification_time": "15:00",
                "default_calendar": "google"
            }
        }

    @pytest.fixture
    def test_event_data(self):
        """Create test event data."""
        return {
            "summary": "Test Event",
            "description": "This is a test event",
            "start_datetime": datetime.utcnow(),
            "end_datetime": datetime.utcnow() + timedelta(hours=1),
            "location": "Test Location",
            "attendees": ["test@example.com"],
            "status": "confirmed"
        }

    @pytest.fixture
    def test_session_data(self):
        """Create test session data."""
        return {
            "provider": "google",
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "https://www.googleapis.com/auth/calendar"
        }

    @pytest.fixture
    def test_agent_log_data(self):
        """Create test agent log data."""
        return {
            "intent": "create_event",
            "entities": {
                "summary": "Test Event",
                "start_time": "2024-03-20T10:00:00Z",
                "end_time": "2024-03-20T11:00:00Z"
            },
            "response": "Event created successfully",
            "processing_time": 0.5,
            "success": True
        }

    async def test_user_model(self, test_db, test_user_data):
        """Test User model operations."""
        # Create user
        user = User(**test_user_data)
        await test_db.users.insert_one(user.dict())
        
        # Retrieve user
        retrieved_user = await test_db.users.find_one({"email": test_user_data["email"]})
        assert retrieved_user is not None
        assert retrieved_user["email"] == test_user_data["email"]
        assert retrieved_user["name"] == test_user_data["name"]
        assert retrieved_user["timezone"] == test_user_data["timezone"]
        
        # Update user
        new_name = "Updated Test User"
        await test_db.users.update_one(
            {"email": test_user_data["email"]},
            {"$set": {"name": new_name}}
        )

    # Verify update
        updated_user = await test_db.users.find_one({"email": test_user_data["email"]})
        assert updated_user["name"] == new_name
        
        # Delete user
        await test_db.users.delete_one({"email": test_user_data["email"]})
        
        # Verify deletion
        deleted_user = await test_db.users.find_one({"email": test_user_data["email"]})
        assert deleted_user is None

    async def test_event_model(self, test_db, test_event_data):
        """Test Event model operations."""
        # Create event
        event = Event(**test_event_data)
        await test_db.events.insert_one(event.dict())
        
        # Retrieve event
        retrieved_event = await test_db.events.find_one({"summary": test_event_data["summary"]})
        assert retrieved_event is not None
        assert retrieved_event["summary"] == test_event_data["summary"]
        assert retrieved_event["description"] == test_event_data["description"]
        assert retrieved_event["status"] == test_event_data["status"]
        
        # Update event
        new_summary = "Updated Test Event"
        await test_db.events.update_one(
            {"summary": test_event_data["summary"]},
            {"$set": {"summary": new_summary}}
        )
        
        # Verify update
        updated_event = await test_db.events.find_one({"summary": new_summary})
        assert updated_event["summary"] == new_summary
        
        # Delete event
        await test_db.events.delete_one({"summary": new_summary})
        
        # Verify deletion
        deleted_event = await test_db.events.find_one({"summary": new_summary})
        assert deleted_event is None

    async def test_session_model(self, test_db, test_session_data):
        """Test Session model operations."""
        # Create session
        session = Session(**test_session_data)
        await test_db.sessions.insert_one(session.dict())
        
        # Retrieve session
        retrieved_session = await test_db.sessions.find_one({"provider": test_session_data["provider"]})
        assert retrieved_session is not None
        assert retrieved_session["provider"] == test_session_data["provider"]
        assert retrieved_session["token_type"] == test_session_data["token_type"]
        assert retrieved_session["scope"] == test_session_data["scope"]
        
        # Update session
        new_token = "new-access-token"
        await test_db.sessions.update_one(
            {"provider": test_session_data["provider"]},
            {"$set": {"access_token": new_token}}
        )
        
        # Verify update
        updated_session = await test_db.sessions.find_one({"provider": test_session_data["provider"]})
        assert updated_session["access_token"] == new_token
        
        # Delete session
        await test_db.sessions.delete_one({"provider": test_session_data["provider"]})
        
        # Verify deletion
        deleted_session = await test_db.sessions.find_one({"provider": test_session_data["provider"]})
        assert deleted_session is None

    async def test_agent_log_model(self, test_db, test_agent_log_data):
        """Test AgentLog model operations."""
        # Create agent log
        agent_log = AgentLog(**test_agent_log_data)
        await test_db.agent_logs.insert_one(agent_log.dict())
        
        # Retrieve agent log
        retrieved_log = await test_db.agent_logs.find_one({"intent": test_agent_log_data["intent"]})
        assert retrieved_log is not None
        assert retrieved_log["intent"] == test_agent_log_data["intent"]
        assert retrieved_log["success"] == test_agent_log_data["success"]
        assert retrieved_log["processing_time"] == test_agent_log_data["processing_time"]
        
        # Update agent log
        new_response = "Updated response"
        await test_db.agent_logs.update_one(
            {"intent": test_agent_log_data["intent"]},
            {"$set": {"response": new_response}}
        )
        
        # Verify update
        updated_log = await test_db.agent_logs.find_one({"intent": test_agent_log_data["intent"]})
        assert updated_log["response"] == new_response
        
        # Delete agent log
        await test_db.agent_logs.delete_one({"intent": test_agent_log_data["intent"]})
        
        # Verify deletion
        deleted_log = await test_db.agent_logs.find_one({"intent": test_agent_log_data["intent"]})
        assert deleted_log is None

    async def test_user_validation(self, test_db):
        """Test User model validation."""
        # Test invalid email
        invalid_user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "timezone": "UTC"
        }
        
        with pytest.raises(ValidationError) as excinfo:
            User(**invalid_user_data)
        
        assert "Invalid email format" in str(excinfo.value)
        
        # Test missing required field
        incomplete_user_data = {
            "email": "test@example.com",
            "name": "Test User"
        }
        
        with pytest.raises(ValidationError) as excinfo:
            User(**incomplete_user_data)
        
        assert "timezone is required" in str(excinfo.value)

    async def test_event_validation(self, test_db):
        """Test Event model validation."""
        # Test invalid datetime
        invalid_event_data = {
            "summary": "Test Event",
            "description": "This is a test event",
            "start_datetime": "invalid-datetime",
            "end_datetime": datetime.utcnow() + timedelta(hours=1),
            "status": "confirmed"
        }
        
        with pytest.raises(ValidationError) as excinfo:
            Event(**invalid_event_data)
        
        assert "Invalid datetime format" in str(excinfo.value)
        
        # Test end time before start time
        invalid_times_event_data = {
            "summary": "Test Event",
            "description": "This is a test event",
            "start_datetime": datetime.utcnow() + timedelta(hours=1),
            "end_datetime": datetime.utcnow(),
            "status": "confirmed"
        }
        
        with pytest.raises(ValidationError) as excinfo:
            Event(**invalid_times_event_data)
        
        assert "End time must be after start time" in str(excinfo.value)

    async def test_session_validation(self, test_db):
        """Test Session model validation."""
        # Test invalid provider
        invalid_session_data = {
            "provider": "invalid-provider",
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "https://www.googleapis.com/auth/calendar"
        }
        
        with pytest.raises(ValidationError) as excinfo:
            Session(**invalid_session_data)
        
        assert "Invalid provider" in str(excinfo.value)
        
        # Test expired token
        expired_session_data = {
            "provider": "google",
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "expires_at": datetime.utcnow() - timedelta(hours=1),
            "scope": "https://www.googleapis.com/auth/calendar"
        }
        
        with pytest.raises(ValidationError) as excinfo:
            Session(**expired_session_data)
        
        assert "Token has expired" in str(excinfo.value)

    async def test_agent_log_validation(self, test_db):
        """Test AgentLog model validation."""
        # Test invalid processing time
        invalid_log_data = {
            "intent": "create_event",
            "entities": {
                "summary": "Test Event",
                "start_time": "2024-03-20T10:00:00Z",
                "end_time": "2024-03-20T11:00:00Z"
            },
            "response": "Event created successfully",
            "processing_time": -0.5,
            "success": True
        }
        
        with pytest.raises(ValidationError) as excinfo:
            AgentLog(**invalid_log_data)
        
        assert "Processing time must be positive" in str(excinfo.value)
        
        # Test missing required field
        incomplete_log_data = {
            "intent": "create_event",
            "entities": {
                "summary": "Test Event"
            },
            "success": True
        }
        
        with pytest.raises(ValidationError) as excinfo:
            AgentLog(**incomplete_log_data)
        
        assert "response is required" in str(excinfo.value) 