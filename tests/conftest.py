"""Test fixtures for the Personal Calendar Assistant."""
from .test_config import setup_test_environment, teardown_test_environment, TEST_USER_DATA, TEST_EVENT_DATA, TEST_SESSION_DATA, TEST_AGENT_LOG_DATA
setup_test_environment()

import os
import pytest
import pytest_asyncio
import uuid
import json
import warnings
from datetime import datetime, time, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import UUID
from typing import Dict, List, Optional, Any, Union, Generator, AsyncGenerator
import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from app.models.mongodb_models import User, Event, Session, AgentLog
from app.core.exceptions import ToolExecutionError
from app.services.encryption import TokenEncryption
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from src.repositories.mongodb_repository import MongoRepository
from src.services.google_calendar_service import GoogleCalendarService
from src.services.microsoft_calendar_service import MicrosoftCalendarService

# Filter out deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Define test user ID
TEST_USER_ID = "11111111-1111-1111-1111-111111111111"

# Define a base datetime for tests
BASE_DATETIME = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

# Define calendar-specific exceptions for testing
class CalendarConflictException(ToolExecutionError):
    """Exception raised when a calendar event conflicts with existing events."""
    pass

class CalendarNotFoundException(ToolExecutionError):
    """Exception raised when a calendar is not found."""
    pass

class TestSettings:
    """Test settings for the app."""
    MONGODB_URI = "mongodb://localhost:27017"
    MONGODB_DB_NAME = "test_calendar_db"
    JWT_SECRET = "test_jwt_secret"
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    ENCRYPTION_KEY = "test_encryption_key_32_chars_long_!"
    GOOGLE_CLIENT_ID = "test_google_client_id"
    GOOGLE_CLIENT_SECRET = "test_google_client_secret"
    GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
    MS_CLIENT_ID = "test_ms_client_id"
    MS_CLIENT_SECRET = "test_ms_client_secret"
    MS_TENANT_ID = "test_tenant_id"
    MS_REDIRECT_URI = "http://localhost:8000/auth/microsoft/callback"
    REDIS_URL = "redis://localhost:6379/0"
    RATE_LIMIT_PER_MINUTE = 60
    DB_ECHO = False

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    setup_test_environment()
    yield
    teardown_test_environment()
    os.environ.pop("TESTING", None)

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def mongodb_client():
    """Create a MongoDB client for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    try:
        # Test connection
        await client.admin.command('ping')
        yield client
    finally:
        client.close()

@pytest_asyncio.fixture(scope="function")
async def test_db(mongodb_client: AsyncIOMotorClient):
    """Create a test database that is dropped after the session."""
    db_name = "calendar_test"
    db = mongodb_client[db_name]
    yield db
    await mongodb_client.drop_database(db_name)

@pytest.fixture
def repository(mongodb_client):
    """Create a repository instance for testing."""
    repo = MongoRepository(mongodb_client)
    # We don't await initialize here as it will be handled in the test
    return repo

@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user for tests and insert it into the database."""
    user_id = ObjectId()
    user_data = {
        "_id": user_id,
        "email": "test@example.com",
        "name": "Test User",
        "google_access_token": "test_google_token",
        "microsoft_access_token": "test_microsoft_token",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "timezone": "UTC",
        "working_hours_start": "09:00",
        "working_hours_end": "17:00",
        "preferences": {}
    }
    
    # Insert the user into the database
    await test_db.users.insert_one(user_data)
    
    # Create a User object with string ID
    user_data["_id"] = str(user_id)
    user = User(**user_data)
    
    return user

@pytest_asyncio.fixture
async def async_test_user(repository):
    """Create a test user for async tests."""
    repo = await repository.initialize()
    user_data = {
        "email": "test@example.com",
        "google_access_token": "test_google_token",
        "microsoft_access_token": "test_microsoft_token"
    }
    user = await repo.create_user(user_data)
    yield user
    # Cleanup
    await repo.users.delete_one({"email": "test@example.com"})

@pytest_asyncio.fixture
async def test_event(test_db, test_user):
    """Create a test event."""
    event_data = TEST_EVENT_DATA.copy()
    event_data["_id"] = ObjectId()
    event_data["user_id"] = str(test_user.id)
    event_data["created_at"] = datetime.utcnow()
    event_data["updated_at"] = datetime.utcnow()
    
    try:
        result = await test_db.events.insert_one(event_data)
        event = Event(**event_data)
        event.id = result.inserted_id
        yield event
    finally:
        await test_db.events.delete_one({"_id": event_data["_id"]})

@pytest_asyncio.fixture
async def test_session(test_db, test_user):
    """Create a test session."""
    session_data = TEST_SESSION_DATA.copy()
    session_data["_id"] = ObjectId()
    session_data["user_id"] = str(test_user.id)
    session_data["created_at"] = datetime.utcnow()
    session_data["updated_at"] = datetime.utcnow()
    
    try:
        result = await test_db.sessions.insert_one(session_data)
        session = Session(**session_data)
        session.id = result.inserted_id
        yield session
    finally:
        await test_db.sessions.delete_one({"_id": session_data["_id"]})

@pytest_asyncio.fixture
async def test_agent_log(test_db, test_user):
    """Create a test agent log."""
    log_data = TEST_AGENT_LOG_DATA.copy()
    log_data["_id"] = ObjectId()
    log_data["user_id"] = str(test_user.id)
    log_data["session_id"] = str(ObjectId())
    log_data["interaction_id"] = str(ObjectId())
    log_data["created_at"] = datetime.utcnow()
    
    try:
        result = await test_db.agent_logs.insert_one(log_data)
        log = AgentLog(**log_data)
        log.id = result.inserted_id
        yield log
    finally:
        await test_db.agent_logs.delete_one({"_id": log_data["_id"]})

@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption

@pytest.fixture
def mock_google_service(mock_token_encryption, test_user, test_db):
    """Create a mock Google Calendar service."""
    service = MockGoogleService(test_user, test_db)
    return service

@pytest.fixture
def mock_microsoft_service(mock_token_encryption, test_user, test_db):
    """Create a mock Microsoft Calendar service."""
    service = MockMicrosoftService("dummy_credentials")
    return service

class MockGoogleService:
    """Mock Google Calendar service for testing."""
    def __init__(self, user, db):
        self.user = user
        self.db = db

    async def list_events(self, time_min=None, time_max=None, calendar_id="primary", max_results=10):
        """Mock list events."""
        return [
            {
                "id": "mock_google_event_1",
                "summary": "Mock Google Event",
                "start": {"dateTime": BASE_DATETIME.isoformat()},
                "end": {"dateTime": (BASE_DATETIME + timedelta(hours=1)).isoformat()},
                "attendees": [{"email": "test@example.com"}],
                "htmlLink": "https://calendar.google.com/event?id=123"
            },
            {
                "id": "mock_google_event_2",
                "summary": "Another Mock Event",
                "start": {"dateTime": (BASE_DATETIME + timedelta(hours=2)).isoformat()},
                "end": {"dateTime": (BASE_DATETIME + timedelta(hours=3)).isoformat()},
                "attendees": [{"email": "test2@example.com"}],
                "htmlLink": "https://calendar.google.com/event?id=124"
            }
        ]

    async def find_free_slots(self, duration_minutes=30, range_start=None, range_end=None, calendar_id="primary"):
        """Mock find free slots."""
        return [
            {
                "start": BASE_DATETIME.isoformat(),
                "end": (BASE_DATETIME + timedelta(minutes=duration_minutes)).isoformat()
            },
            {
                "start": (BASE_DATETIME + timedelta(hours=4)).isoformat(),
                "end": (BASE_DATETIME + timedelta(hours=4, minutes=duration_minutes)).isoformat()
            }
        ]

    async def create_event(self, event_data, calendar_id="primary"):
        """Mock create event."""
        # Process attendees properly
        attendees = []
        if "attendees" in event_data:
            for attendee in event_data["attendees"]:
                if isinstance(attendee, dict):
                    attendees.append(attendee)
                else:
                    attendees.append({"email": attendee["email"] if isinstance(attendee, dict) else attendee})
        
        return {
            "id": "mock_google_event_2",
            "summary": event_data["summary"],
            "start": event_data["start"],
            "end": event_data["end"],
            "attendees": attendees,
            "htmlLink": "https://calendar.google.com/event?id=125"
        }
    
    async def update_event(self, event_id, event_data, calendar_id="primary"):
        """Mock update event."""
        return {
            "id": event_id,
            "summary": event_data.get("summary", "Updated Event"),
            "start": event_data.get("start", BASE_DATETIME.isoformat()),
            "end": event_data.get("end", (BASE_DATETIME + timedelta(hours=1)).isoformat()),
            "attendees": event_data.get("attendees", []),
            "htmlLink": "https://calendar.google.com/event?id=126"
        }
    
    async def delete_event(self, event_id, calendar_id="primary"):
        """Mock delete event."""
        return True
        
    async def cancel_event(self, event_id, calendar_id="primary", start=None, end=None):
        """Mock cancel event."""
        return True

class MockMicrosoftService:
    """Mock Microsoft Calendar service for testing."""
    
    def __init__(self, credentials):
        self.credentials = credentials
    
    async def list_events(self, time_min=None, time_max=None, calendar_id="primary", max_results=10):
        """Mock list events."""
        return [
            {
                "id": "mock_ms_event_1",
                "summary": "Mock MS Event",
                "start": {"dateTime": BASE_DATETIME.isoformat()},
                "end": {"dateTime": (BASE_DATETIME + timedelta(hours=1)).isoformat()},
                "attendees": [{"email": "test@example.com"}],
                "htmlLink": "https://outlook.office.com/calendar/event/123"
            }
        ]
    
    async def find_free_slots(self, duration_minutes=30, range_start=None, range_end=None, calendar_id="primary"):
        """Mock find free slots."""
        return [
            {
                "start": BASE_DATETIME.isoformat(),
                "end": (BASE_DATETIME + timedelta(minutes=duration_minutes)).isoformat()
            },
            {
                "start": (BASE_DATETIME + timedelta(hours=4)).isoformat(),
                "end": (BASE_DATETIME + timedelta(hours=4, minutes=duration_minutes)).isoformat()
            }
        ]
    
    async def create_event(self, event_data, calendar_id="primary"):
        """Mock create event."""
        return {
            "id": "mock_ms_event_2",
            "summary": event_data.get("summary", "New Event"),
            "start": event_data.get("start", BASE_DATETIME.isoformat()),
            "end": event_data.get("end", (BASE_DATETIME + timedelta(hours=1)).isoformat()),
            "attendees": event_data.get("attendees", []),
            "htmlLink": "https://outlook.office.com/calendar/event/125"
        }
    
    async def update_event(self, event_id, event_data, calendar_id="primary"):
        """Mock update event."""
        return {
            "id": event_id,
            "summary": event_data.get("summary", "Updated Event"),
            "start": event_data.get("start", BASE_DATETIME.isoformat()),
            "end": event_data.get("end", (BASE_DATETIME + timedelta(hours=1)).isoformat()),
            "attendees": event_data.get("attendees", []),
            "htmlLink": "https://outlook.office.com/calendar/event/126"
        }
    
    async def delete_event(self, event_id, calendar_id="primary"):
        """Mock delete event."""
        return True
        
    async def cancel_event(self, event_id, calendar_id="primary", start=None, end=None):
        """Mock cancel event."""
        return True

@pytest.fixture(autouse=True)
def patch_services(mock_google_service, mock_microsoft_service):
    """Patch calendar services for testing."""
    with patch("app.services.google_calendar.GoogleCalendarService", return_value=mock_google_service), \
         patch("app.services.ms_calendar.MicrosoftCalendarService", return_value=mock_microsoft_service):
        yield

@pytest.fixture
def client():
    """Return a TestClient instance for the app."""
    return TestClient(app)

@pytest.fixture
def mock_llm_selector():
    mock = MagicMock()
    mock.generate_with_fallback = MagicMock(return_value={"mock": "llm_response"})
    return mock

@pytest.fixture
def mock_langgraph_runner():
    """Create a mock LangGraph runner."""
    runner = MagicMock()
    # The rest of the mock implementation would go here
    return runner

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(test_db: AsyncIOMotorDatabase):
    """Fixture to ensure the test database is clean before each test."""
    # This fixture can be used to clear collections before each test if needed
    collections = ['users', 'events', 'sessions', 'agent_logs', 'oauth_states']
    
    # Get the list of collections first
    collection_names = []
    # Await the coroutine properly instead of using async for
    cursor = await test_db.list_collections()
    async for collection in cursor:
        collection_names.append(collection["name"])
    
    # Then delete data from each collection that exists
    for collection in collections:
        if collection in collection_names:
            await test_db.drop_collection(collection)
    
    yield test_db

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.query = MagicMock(return_value=db)
    db.filter = MagicMock(return_value=db)
    db.first = MagicMock(return_value=None)
    db.all = MagicMock(return_value=[])
    return db

@pytest.fixture
def google_service():
    """Create a mock Google Calendar service."""
    service = MagicMock(spec=GoogleCalendarService)
    service.list_events = AsyncMock(return_value=[{"id": "test_event_id"}])
    service.find_free_slots = AsyncMock(return_value=[{"start": "2023-01-01T10:00:00Z", "end": "2023-01-01T11:00:00Z"}])
    service.create_event = AsyncMock(return_value={"id": "new_event_id"})
    service.update_event = AsyncMock(return_value={"id": "updated_event_id"})
    service.delete_event = AsyncMock(return_value=True)
    return service

@pytest.fixture
def microsoft_service():
    """Create a mock Microsoft Calendar service."""
    service = MagicMock(spec=MicrosoftCalendarService)
    service.list_events = AsyncMock(return_value=[{"id": "test_event_id"}])
    service.find_free_slots = AsyncMock(return_value=[{"start": "2023-01-01T10:00:00Z", "end": "2023-01-01T11:00:00Z"}])
    service.create_event = AsyncMock(return_value={"id": "new_event_id"})
    service.update_event = AsyncMock(return_value={"id": "updated_event_id"})
    service.delete_event = AsyncMock(return_value=True)
    return service

@pytest.fixture
def token_encryption():
    """Create a TokenEncryption instance for testing."""
    return TokenEncryption.get_instance("test_key_12345678901234567890123456789012") 