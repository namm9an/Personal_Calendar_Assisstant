"""Test fixtures for the Personal Calendar Assistant."""
from .test_config import setup_test_environment, teardown_test_environment, TEST_USER_DATA, TEST_EVENT_DATA, TEST_SESSION_DATA, TEST_AGENT_LOG_DATA
setup_test_environment()

import os
import pytest
import uuid
import json
import warnings
from datetime import datetime, time, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import UUID
from typing import Dict, List, Optional, Any, Union, Generator, AsyncGenerator
import logging
import time
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.models.mongodb_models import User, Event, Session, AgentLog
from app.core.exceptions import ToolExecutionError
from app.services.encryption import TokenEncryption
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy.orm import Session
from app.db.connection import get_db
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

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    setup_test_environment()
    yield
    teardown_test_environment()
    os.environ.pop("TESTING", None)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def mongodb_client():
    """Create a MongoDB client for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    try:
        yield client
    finally:
        await client.drop_database("test_calendar_db")
        await client.close()

@pytest.fixture(scope="session")
async def test_db(mongodb_client):
    """Create a test database."""
    db = mongodb_client[os.getenv("MONGODB_DB_NAME", "test_calendar_db")]
    try:
        yield db
    finally:
        await db.client.drop_database(os.getenv("MONGODB_DB_NAME", "test_calendar_db"))

@pytest.fixture
async def repository(mongodb_client):
    """Create a repository instance for testing."""
    repo = MongoRepository(mongodb_client)
    await repo.initialize()
    return repo

@pytest.fixture
async def test_user(repository):
    """Create a test user."""
    user = {
        "email": "test@example.com",
        "google_access_token": "test_google_token",
        "microsoft_access_token": "test_microsoft_token"
    }
    created_user = await repository.create_user(user)
    return created_user

@pytest.fixture
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

@pytest.fixture
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

@pytest.fixture
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
            }
        ]

    async def create_event(self, event_data):
        """Mock create event."""
        return {
            "id": "mock_google_event_2",
            "summary": event_data["summary"],
            "start": {"dateTime": event_data["start"]},
            "end": {"dateTime": event_data["end"]},
            "attendees": [{"email": a} for a in event_data.get("attendees", [])],
            "htmlLink": "https://calendar.google.com/event?id=456"
        }

    async def update_event(self, event_id, event_data):
        """Mock update event."""
        return {
            "id": event_id,
            "summary": event_data["summary"],
            "start": {"dateTime": event_data["start"]},
            "end": {"dateTime": event_data["end"]},
            "attendees": [{"email": a} for a in event_data.get("attendees", [])],
            "htmlLink": "https://calendar.google.com/event?id=789"
        }

    async def delete_event(self, event_id):
        """Mock delete event."""
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
                "subject": "Mock MS Event",
                "start": {"dateTime": BASE_DATETIME.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": (BASE_DATETIME + timedelta(hours=1)).isoformat(), "timeZone": "UTC"},
                "attendees": [{"emailAddress": {"address": "test@example.com"}}],
                "webLink": "https://outlook.office.com/calendar/item/123"
            }
        ]

    async def create_event(self, event_data):
        """Mock create event."""
        return {
            "id": "mock_ms_event_2",
            "subject": event_data["subject"],
            "start": {"dateTime": event_data["start"], "timeZone": "UTC"},
            "end": {"dateTime": event_data["end"], "timeZone": "UTC"},
            "attendees": [{"emailAddress": {"address": a}} for a in event_data.get("attendees", [])],
            "webLink": "https://outlook.office.com/calendar/item/456"
        }

    async def update_event(self, event_id, event_data):
        """Mock update event."""
        return {
            "id": event_id,
            "subject": event_data["subject"],
            "start": {"dateTime": event_data["start"], "timeZone": "UTC"},
            "end": {"dateTime": event_data["end"], "timeZone": "UTC"},
            "attendees": [{"emailAddress": {"address": a}} for a in event_data.get("attendees", [])],
            "webLink": "https://outlook.office.com/calendar/item/789"
        }

    async def delete_event(self, event_id):
        """Mock delete event."""
        return True

@pytest.fixture(autouse=True)
def patch_services(mock_google_service, mock_microsoft_service):
    """Patch calendar services for testing."""
    with patch("app.services.google_calendar.GoogleCalendarService", return_value=mock_google_service), \
         patch("app.services.ms_calendar.MicrosoftCalendarService", return_value=mock_microsoft_service):
        yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_llm_selector():
    mock = MagicMock()
    mock.generate_with_fallback = MagicMock(return_value={"mock": "llm_response"})
    return mock

@pytest.fixture
def mock_langgraph_runner():
    mock = MagicMock()
    mock.run_stream = MagicMock(return_value=iter([{"message": "step", "tool": None, "input": None, "output": None}]))
    return mock

@pytest.fixture(scope="session")
async def db_session() -> AsyncGenerator[Session, None]:
    """Create a fresh database session for a test."""
    async for session in get_db():
        yield session

@pytest.fixture(autouse=True)
async def setup_test_db(db_session: Session):
    """Set up test database and clean up after tests."""
    # Setup
    yield
    # Cleanup
    await db_session.rollback()
    await db_session.close()

@pytest.fixture
def mock_db():
    """Create a mock database session for testing."""
    class MockSession:
        def __init__(self):
            self.query = lambda x: self
            self.filter = lambda x: self
            self.first = lambda: None
            self.all = lambda: []
            self.add = lambda x: None
            self.commit = lambda: None
            self.rollback = lambda: None
            self.close = lambda: None
    return MockSession()

@pytest.fixture
async def google_service():
    """Create a mock Google Calendar service."""
    service = GoogleCalendarService()
    return service

@pytest.fixture
async def microsoft_service():
    """Create a mock Microsoft Calendar service."""
    service = MicrosoftCalendarService()
    return service

@pytest.fixture
def token_encryption():
    """Create a TokenEncryption instance for testing."""
    return TokenEncryption.get_instance("test_key_12345678901234567890123456789012") 