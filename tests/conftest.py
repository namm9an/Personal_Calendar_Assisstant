import os
import pytest
import uuid
import json
import sqlite3
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch
from uuid import UUID
from typing import Dict, List, Optional, Any, Union
import logging
import time
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.db.connection import mongodb
from src.models.mongodb_models import User, Event, Session, AgentLog
from bson import ObjectId

import sqlalchemy
from sqlalchemy import create_engine, event, Column, String
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import func

from app.models.user import User
from app.models.calendar import UserCalendar, CalendarAction
from app.schemas.tool_schemas import EventSchema, FreeSlotSchema, AttendeeSchema
from app.schemas.calendar import EventCreate, EventUpdate, TimeSlot
from app.db.postgres import Base  # This imports all models that inherit from Base
from app.core.exceptions import ToolExecutionError
from app.models.types import UniversalUUID
from app.services.encryption import TokenEncryption # Added for type hinting if needed

# Register UUID type with SQLite
try:
    import sqlite3
    
    def adapt_uuid(uuid_obj):
        """Convert UUID to string for SQLite storage."""
        if uuid_obj is None:
            return None
        return str(uuid_obj)

    def convert_uuid(text):
        """Convert SQLite string to UUID."""
        if text is None:
            return None
        try:
            return uuid.UUID(text)
        except (ValueError, TypeError):
            return None
    
    # Register the adapter and converter with SQLite
    sqlite3.register_adapter(uuid.UUID, adapt_uuid)
    sqlite3.register_converter("UUID", convert_uuid)
    
except ImportError:
    pass

# Define test user ID
TEST_USER_ID = "11111111-1111-1111-1111-111111111111"

# Define calendar-specific exceptions for testing
class CalendarConflictException(ToolExecutionError):
    """Exception raised when a calendar event conflicts with existing events."""
    pass

class CalendarNotFoundException(ToolExecutionError):
    """Exception raised when a calendar is not found."""
    pass

# Define the SQLite handler function
def setup_sqlite_handlers(dbapi_connection, connection_record):
    if dbapi_connection is not None:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

# Database setup
@pytest.fixture(scope="session")
def db_engine():
    """Create a SQLite in-memory database for testing."""
    # Force SQLite for tests regardless of environment settings
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SQLALCHEMY_WARN_20'] = '1'  # Enable SQLAlchemy 2.0 warnings
    
    # Always use SQLite in-memory database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            "uri": True
        },
        echo=False  # Set to False to reduce noise in test output
    )
    
    # Register event listener for SQLite pragmas
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            # Ensure text factory returns strings
            dbapi_connection.text_factory = str
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    # Create a scoped session bound to this connection
    Session = scoped_session(sessionmaker(bind=connection))
    session = Session()
    
    yield session
    
    # Rollback transaction and cleanup
    session.close()
    transaction.rollback()
    connection.close()
    Session.remove()

@pytest.fixture
def test_user(db_session, mock_token_encryption: TokenEncryption):
    """Create a test user with a fixed UUID and mocked encrypted tokens."""
    user = User(
        id=uuid.UUID(TEST_USER_ID),
        email="test@example.com",
        name="Test User",
        timezone="UTC",
        working_hours_start=time(9, 0),
        working_hours_end=time(17, 0),
        # Add encrypted tokens using the mock_token_encryption fixture
        google_access_token=mock_token_encryption.encrypt("dummy_google_access_token"),
        google_refresh_token=mock_token_encryption.encrypt("dummy_google_refresh_token"),
        microsoft_access_token=mock_token_encryption.encrypt("dummy_microsoft_access_token"),
        microsoft_refresh_token=mock_token_encryption.encrypt("dummy_microsoft_refresh_token")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user) # Ensure all attributes are loaded, like generated IDs if any
    return user

@pytest.fixture
def test_user_calendar(db_session, test_user):
    """Create a test calendar for the test user."""
    calendar = UserCalendar(
        user_id=test_user.id,
        provider="google",
        calendar_id="primary",
        name="Test Calendar",
        is_primary=True
    )
    db_session.add(calendar)
    db_session.commit()
    
    return calendar

@pytest.fixture
def test_calendar_action(db_session, test_user):
    """Create a test calendar action for the test user."""
    action = CalendarAction(
        user_id=test_user.id,
        provider="google",
        action_type="list",
        event_id="test-event-id",
        event_summary="Test Event",
        event_start=datetime.now(),
        event_end=datetime.now() + timedelta(hours=1),
        success=True
    )
    db_session.add(action)
    db_session.commit()
    
    return action

# --- Mock Services and Related Fixtures (As per Phase 3 Task 2 Plan) ---

class MockGoogleService:
    def __init__(self, user: User, db_session: Session):
        self.user = user
        self.db_session = db_session
        self.token = "decrypted_google_token_from_mock"
        self.events = []

    def list_events(self, calendar_id: str, time_min: datetime, time_max: datetime, max_results: int):
        # Simulates returning a list of EventSchema-like dicts
        return [
            {
                "id": "google_event_1", "summary": "Google Event 1",
                "start": datetime.utcnow() + timedelta(hours=1),
                "end": datetime.utcnow() + timedelta(hours=2),
                "attendees": [{"email": "att1@example.com", "name": "Attendee 1"}]
            },
            {
                "id": "google_event_2", "summary": "Google Event 2",
                "start": datetime.utcnow() + timedelta(days=1, hours=1),
                "end": datetime.utcnow() + timedelta(days=1, hours=2),
                "attendees": []
            }
        ]

    def find_free_slots(self, calendar_id: str, time_min: datetime, time_max: datetime, duration_minutes: int, user_id: str):
        return [
            {"start": datetime.utcnow() + timedelta(hours=4), "end": datetime.utcnow() + timedelta(hours=4, minutes=30)},
            {"start": datetime.utcnow() + timedelta(days=1, hours=4), "end": datetime.utcnow() + timedelta(days=1, hours=4, minutes=30)}
        ]

    def create_event(self, event_create: Any, calendar_id: str = "primary") -> Dict[str, Any]:
        logger.info(f"MockGoogleService: create_event called with summary: {event_create.summary}")
        event_id = f"google_event_{int(time.time())}_{self.user.id[:4]}"
        
        # Convert EventCreate's TimeSlot to the dictionary structure expected in response
        start_iso = event_create.time_slot.start.isoformat()
        end_iso = event_create.time_slot.end.isoformat()

        new_event_data = {
            "id": event_id,
            "summary": event_create.summary,
            "description": event_create.description,
            "location": event_create.location,
            "start": {"dateTime": start_iso, "timeZone": event_create.time_zone or self.user.time_zone or "UTC"},
            "end": {"dateTime": end_iso, "timeZone": event_create.time_zone or self.user.time_zone or "UTC"},
            "attendees": [att.model_dump() for att in event_create.attendees] if event_create.attendees else [],
            "htmlLink": f"https://calendar.google.com/event?eid={event_id}",
            "organizer": {"email": self.user.email, "self": True},
            "creator": {"email": self.user.email, "self": True},
            "status": event_create.status.value if event_create.status else "confirmed",
            # conferenceData is now part of EventCreate schema
        }
        if event_create.conference_data:
            new_event_data["conferenceData"] = event_create.conference_data
        
        self.events.append(new_event_data)
        # This method, as part of the *service layer* mock, should return a dictionary.
        # CalendarTools will then json.dumps this dictionary.
        return new_event_data

    # Add get_events alias for consistency if list_events is also used by CalendarTools
    def get_events(self, calendar_id: str, time_min: datetime, time_max: datetime, max_results: int):
        return self.list_events(calendar_id, time_min, time_max, max_results)

    def update_event(self, event_id: str, event_update: Any, calendar_id: str = "primary") -> Dict[str, Any]:
        logger.info(f"MockGoogleService: update_event called for event_id: {event_id}")

        if event_id == "invalid-google-event-id":
            # Simulate Google API's HttpError for event not found
            # Construct a mock HttpError response object
            mock_resp = MagicMock()
            mock_resp.status = 404
            mock_resp.reason = "Not Found"
            # The content can be a JSON string or bytes, depending on what GoogleHttpError expects
            # For simplicity, we'll assume it can take a string detail for its constructor or message.
            # A more accurate mock might involve creating a proper `httplib2.Response` object.
            raise GoogleHttpError(resp=mock_resp, content=b'{"error": {"errors": [{"domain": "global", "reason": "notFound", "message": "Not Found"}], "code": 404, "message": "Not Found"}}')

        original_event = next((e for e in self.events if e["id"] == event_id), None)
        if not original_event:
            # This case should ideally be covered by the 'invalid-google-event-id' check for testing specific error handling
            # but as a general fallback for other IDs not in self.events:
            mock_resp = MagicMock()
            mock_resp.status = 404
            mock_resp.reason = "Not Found"
            raise GoogleHttpError(resp=mock_resp, content=b'{"error": {"errors": [{"domain": "global", "reason": "notFound", "message": "Not Found by fallback"}], "code": 404, "message": "Not Found by fallback"}}')

        # Apply updates (simplified)
        if event_update.start:
            original_event["start"] = {"dateTime": event_update.start.isoformat(), "timeZone": event_update.time_zone or self.user.time_zone or "UTC"}
        if event_update.end:
            original_event["end"] = {"dateTime": event_update.end.isoformat(), "timeZone": event_update.time_zone or self.user.time_zone or "UTC"}
        if event_update.summary:
            original_event["summary"] = event_update.summary
        if event_update.description:
            original_event["description"] = event_update.description
        if event_update.location:
            original_event["location"] = event_update.location
        if event_update.attendees:
            original_event["attendees"] = [att.model_dump() for att in event_update.attendees]

        return original_event

    def delete_event(self, event_id: str, calendar_id: str):
        # For Google, delete usually returns nothing on success
        return None

class MockMicrosoftService:
    def __init__(self, credentials: str): # Microsoft service might take credentials differently
        self.credentials = credentials

    def list_events(self, user_id: str, calendar_id: str, time_min: datetime, time_max: datetime, max_results: int):
        return [
            {
                "id": "ms_event_1", "summary": "Microsoft Event 1",
                "start": datetime.utcnow() + timedelta(hours=1),
                "end": datetime.utcnow() + timedelta(hours=2),
                "attendees": [{"email": "att_ms1@example.com", "name": "MS Attendee 1"}]
            }
        ]

    def find_free_slots(self, user_id: str, calendar_id: str, time_min: datetime, time_max: datetime, duration_minutes: int):
        return [
            {"start": datetime.utcnow() + timedelta(hours=5), "end": datetime.utcnow() + timedelta(hours=5, minutes=30)}
        ]

    def create_event(self, event_create: Any, calendar_id: str = "primary") -> Dict[str, Any]:
        logger.info(f"MockMicrosoftService: create_event called with summary: {event_create.summary}")
        event_id = f"ms_event_{int(time.time())}_{self.user.id[:4]}"

        start_iso = event_create.time_slot.start.isoformat()
        end_iso = event_create.time_slot.end.isoformat()

        new_event_data = {
            "id": event_id,
            "subject": event_create.summary, # Microsoft uses 'subject'
            "body": {"contentType": "HTML", "content": event_create.description or ""},
            "location": {"displayName": event_create.location or ""},
            "start": {"dateTime": start_iso, "timeZone": event_create.time_zone or self.user.time_zone or "UTC"},
            "end": {"dateTime": end_iso, "timeZone": event_create.time_zone or self.user.time_zone or "UTC"},
            "attendees": [
                {"emailAddress": {"address": att.email, "name": att.name}, "type": "required"}
                for att in event_create.attendees
            ] if event_create.attendees else [],
            "webLink": f"https://outlook.office.com/calendar/event/{event_id}",
            "organizer": {"emailAddress": {"address": self.user.email, "name": self.user.name}},
            # conferenceData is now part of EventCreate schema
        }
        if event_create.conference_data:
            new_event_data["conferenceData"] = event_create.conference_data

        self.events.append(new_event_data)
        # This method, as part of the *service layer* mock, should return a dictionary.
        return new_event_data

    # Add get_events alias for consistency if list_events is also used by CalendarTools
    def get_events(self, user_id: str, calendar_id: str, time_min: datetime, time_max: datetime, max_results: int):
        return self.list_events(user_id, calendar_id, time_min, time_max, max_results)

    def update_event(self, event_id: str, event_update: Any, calendar_id: str = "primary") -> Dict[str, Any]:
        logger.info(f"MockMicrosoftService: update_event called for event_id: {event_id}")

        if event_id == "invalid-ms-event-id":
            raise HTTPException(
                status_code=404, 
                detail="Microsoft Graph API: Event not found."
            )

        original_event = next((e for e in self.events if e["id"] == event_id), None)
        if not original_event:
            # Fallback for other non-existent IDs
            raise HTTPException(
                status_code=404, 
                detail="MockMicrosoftService: Event not found by fallback."
            )

        # Apply updates (simplified)
        if event_update.start:
            original_event["start"] = {"dateTime": event_update.start.isoformat(), "timeZone": event_update.time_zone or self.user.time_zone or "UTC"}
        if event_update.end:
            original_event["end"] = {"dateTime": event_update.end.isoformat(), "timeZone": event_update.time_zone or self.user.time_zone or "UTC"}
        if event_update.summary:
            original_event["subject"] = event_update.summary
        if event_update.description:
            original_event["body"] = {"contentType": "HTML", "content": event_update.description}
        if event_update.location:
            original_event["location"] = {"displayName": event_update.location}
        if event_update.attendees:
            original_event["attendees"] = [
                {"emailAddress": {"address": att.email, "name": att.name}, "type": "required"}
                for att in event_update.attendees
            ]

        return original_event

    def delete_event(self, user_id: str, event_id: str, calendar_id: str):
        return None # Assuming similar behavior to Google

@pytest.fixture
def mock_token_encryption(monkeypatch):
    class MockTokenEncryption:
        def decrypt(self, ciphertext):
            if ciphertext is None or ciphertext == "bad_token_ciphertext":
                return None
            # Basic check if it looks like our dummy encrypted token
            if ciphertext == "dummy_ciphertext_google_access_token" or \
               ciphertext == "dummy_ciphertext_google_refresh_token" or \
               ciphertext == "dummy_ciphertext_microsoft_access_token" or \
               ciphertext == "dummy_ciphertext_microsoft_refresh_token":
                # Simplified: just return a generic valid token for any valid-looking ciphertext
                return "decrypted_dummy_token" 
            return "decrypted_dummy_token" # Default for other non-None, non-bad ciphertexts

        def encrypt(self, plaintext):
            if plaintext is None:
                return None # Or could be "bad_token_ciphertext"
            if plaintext == "dummy_google_access_token":
                return "dummy_ciphertext_google_access_token"
            if plaintext == "dummy_google_refresh_token":
                return "dummy_ciphertext_google_refresh_token"
            if plaintext == "dummy_microsoft_access_token":
                return "dummy_ciphertext_microsoft_access_token"
            if plaintext == "dummy_microsoft_refresh_token":
                return "dummy_ciphertext_microsoft_refresh_token"
            return f"dummy_ciphertext_{plaintext[:10]}" # Generic encryption for other plaintexts

    monkeypatch.setattr("app.services.encryption.TokenEncryption", MockTokenEncryption)
    # Return an instance if needed by the fixture user, or the class itself if preferred
    return MockTokenEncryption() # Return an instance

@pytest.fixture
def mock_google_service(mock_token_encryption, test_user, db_session):
    # The plan is to replace the actual service with our MockGoogleService instance
    # when the app tries to instantiate it.
    def service_factory(*args, **kwargs):
        # The actual GoogleCalendarService takes (user, db_session)
        # Our mock can take them too for consistency or specific mock logic if needed.
        # Here, we pass the test_user and db_session from fixtures.
        return MockGoogleService(user=test_user, db_session=db_session)

    with patch('app.services.google_calendar.GoogleCalendarService', side_effect=service_factory) as mock_patch:
        # Yield the factory itself or an instance if preferred, but yielding the patch
        # allows for assertions on the patch object (e.g., call_count) if needed elsewhere.
        # For direct use of the mock instance in tests, it's better to yield an instance.
        # However, the tool wrappers will instantiate the service, so the side_effect is key.
        yield mock_patch # Tests will interact with the instance created by side_effect

@pytest.fixture
def mock_microsoft_service(mock_token_encryption, test_user, db_session):
    def service_factory(*args, **kwargs):
        # The actual MicrosoftCalendarService might take (credentials) or (user, db_session)
        # Our mock takes credentials for now, matching the current tools.py instantiation
        return MockMicrosoftService(credentials="decrypted_dummy_token")

    with patch('app.services.microsoft_calendar.MicrosoftCalendarService', side_effect=service_factory) as mock_patch:
        yield mock_patch

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def mongodb_client():
    """Create a MongoDB client for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    await client.drop_database("calendar_test")
    client.close()

@pytest.fixture(scope="session")
async def test_db(mongodb_client):
    """Create a test database."""
    db = mongodb_client.calendar_test
    yield db
    await db.client.drop_database("calendar_test")

@pytest.fixture
async def mongodb_repository(test_db):
    """Create a repository instance with test database."""
    mongodb.db = test_db
    return mongodb

@pytest.fixture
async def test_user(mongodb_repository):
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        timezone="UTC"
    )
    result = await mongodb_repository.db.users.insert_one(user.dict(by_alias=True, exclude={'id'}))
    user.id = result.inserted_id
    return user

@pytest.fixture
async def test_event(mongodb_repository, test_user):
    """Create a test event."""
    event = Event(
        user_id=test_user.id,
        provider="google",
        provider_event_id="test_event_1",
        summary="Test Event",
        start=datetime.utcnow(),
        end=datetime.utcnow() + timedelta(hours=1)
    )
    result = await mongodb_repository.db.events.insert_one(event.dict(by_alias=True, exclude={'id'}))
    event.id = result.inserted_id
    return event

@pytest.fixture
async def test_session(mongodb_repository, test_user):
    """Create a test session."""
    session = Session(
        user_id=test_user.id,
        provider="google",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    result = await mongodb_repository.db.sessions.insert_one(session.dict(by_alias=True, exclude={'id'}))
    session.id = result.inserted_id
    return session

@pytest.fixture
async def test_agent_log(mongodb_repository, test_user):
    """Create a test agent log."""
    log = AgentLog(
        user_id=test_user.id,
        intent="list_events",
        input_text="Show my events",
        steps=[{"step": 1, "action": "list_events"}],
        final_output="Found 1 event"
    )
    result = await mongodb_repository.db.agent_logs.insert_one(log.dict(by_alias=True, exclude={'id'}))
    log.id = result.inserted_id
    return log