"""Tests for calendar tool wrappers with MongoDB."""
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

import pytest
import pytest_asyncio
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from src.core.exceptions import ToolExecutionError

from app.models.mongodb_models import User, Event
from src.calendar_tool_wrappers import (
    list_events_tool, find_free_slots_tool, create_event_tool, 
    reschedule_event_tool, cancel_event_tool,
    ListEventsInput, ListEventsOutput, EventSchema,
    FreeSlotsInput, FreeSlotsOutput, FreeSlotSchema,
    CreateEventInput, CreateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput
)

# Constants
PROVIDERS = ["google", "microsoft"]

# Helper functions
async def create_event_in_db(db, user_id, provider, summary):
    """Helper to create a test event in the database."""
    event_id = ObjectId()
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=1)
    event_data = {
        "_id": str(event_id),
        "summary": summary,
        "description": f"Test event for {provider}",
        "user_id": user_id,
        "provider": provider,
        "start_datetime": start_time,
        "end_datetime": end_time,
        "timezone": "UTC",
        "created_by": "test@example.com",
        "provider_event_id": f"test-event-{event_id}",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert into MongoDB with ObjectId as _id
    mongo_data = event_data.copy()
    mongo_data["_id"] = event_id
    
    await db.events.insert_one(mongo_data)
    
    return Event(**event_data)

async def get_event_from_db(db: AsyncIOMotorDatabase, event_id: str) -> Event:
    """Get an event from the database."""
    event_data = await db.events.find_one({"_id": ObjectId(event_id)})
    return Event(**event_data) if event_data else None

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_list_events_tool_happy_path(
    provider_name: str,
    test_db: AsyncIOMotorDatabase,
    test_user: User,
    mock_google_service,
    mock_microsoft_service
):
    """Test the list_events_tool with a valid user and provider."""
    # Create some events in the database
    await create_event_in_db(test_db, str(test_user.id), provider_name, "Test Event 1")
    await create_event_in_db(test_db, str(test_user.id), provider_name, "Test Event 2")
    
    # Test the tool
    now = datetime.utcnow()
    input_data = ListEventsInput(
        provider=provider_name,
        user_id=str(test_user.id),
        start=now,
        end=now + timedelta(hours=24)
    )
    
    # Call the tool
    result = await list_events_tool(input_data)
    
    # Check the result
    assert isinstance(result, ListEventsOutput)
    assert len(result.events) > 0
    for event in result.events:
        assert isinstance(event, EventSchema)
        if provider_name == "google":
            assert event.summary in ["Test Event 1", "Test Event 2", "Mock Google Event", "Another Mock Event"]
        else:
            assert event.summary in ["Test Event 1", "Test Event 2", "Mock MS Event"]

@pytest.mark.asyncio
async def test_list_events_tool_invalid_provider(test_user: User):
    """Test list_events_tool with an invalid provider."""
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="invalid_provider",
            user_id=str(test_user.id),
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "Unsupported provider" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_user_not_found(test_db):
    """Test list_events_tool when user is not found."""
    # Non-existent user ID
    non_existent_id = str(ObjectId())
    
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=non_existent_id,
            start=datetime.utcnow().isoformat(),
            end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        ))
    
    assert "User not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_google_missing_credentials(test_db, test_user):
    """Test list_events_tool with missing Google credentials."""
    # Create a user without Google credentials
    user_without_creds = await test_db.users.insert_one({
        "_id": ObjectId(),
        "email": "no-google@example.com",
        "name": "No Google User",
        # No google_access_token
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=str(user_without_creds.inserted_id),
            start=datetime.utcnow().isoformat(),
            end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        ))
    
    assert "No google credentials available" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_list_events_tool_microsoft_success(mock_microsoft_service, mock_get_user_by_id):
    """Test list_events_tool with a Microsoft provider."""
    # Create a test user
    user_id = str(ObjectId())
    
    # Patch the get_user_by_id method in the calendar_tool_wrappers module
    with patch("src.calendar_tool_wrappers.OAuthService.get_user_by_id", return_value=mock_get_user_by_id(user_id)):
        input_data = ListEventsInput(
            provider="microsoft",
            user_id=user_id,
            start=datetime.utcnow(),
            end=datetime.utcnow() + timedelta(hours=1),
        )
        output = await list_events_tool(input_data)
        
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 1
        assert output.events[0].id == "mock_ms_event_1"
        assert output.events[0].summary == "Mock MS Event"

@pytest.mark.asyncio
async def test_list_events_tool_transient_error(mock_google_service):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Simulate transient error (e.g., Timeout) on first two calls, then success
    mock_google_service.list_events = AsyncMock(side_effect=[
        TimeoutError(), 
        TimeoutError(), 
        [{"id": "1", "summary": "Test Event", "start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(hours=1)}]
    ])
    now = datetime.utcnow()
    input_data = ListEventsInput(
        provider="google",
        user_id=user_id,
        start=now,
        end=now + timedelta(hours=1),
    )
    output = await list_events_tool(input_data)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 1

@pytest.mark.asyncio
async def test_list_events_tool_permanent_error(mocker, test_db, test_user):
    """Test list_events_tool with a permanent error."""
    mocker.patch(
        "src.calendar_tool_wrappers.get_calendar_service",
        return_value=AsyncMock(
            list_events=AsyncMock(side_effect=ValueError("Invalid payload"))
        )
    )
    
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=str(test_user.id),
            start=datetime.utcnow().isoformat(),
            end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        ))
    
    assert "Failed to list events" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_google_success(mock_google_service):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    now = datetime.utcnow()
    input_data = FreeSlotsInput(
        provider="google",
        user_id=user_id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(hours=2)
    )
    output = await find_free_slots_tool(input_data)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) > 0
    assert all(isinstance(slot, FreeSlotSchema) for slot in output.slots)

@pytest.mark.asyncio
async def test_find_free_slots_tool_microsoft_success(mock_microsoft_service):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        microsoft_access_token="test_microsoft_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    now = datetime.utcnow()
    input_data = FreeSlotsInput(
        provider="microsoft",
        user_id=user_id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(hours=2)
    )
    output = await find_free_slots_tool(input_data)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) > 0
    assert all(isinstance(slot, FreeSlotSchema) for slot in output.slots)

@pytest.mark.asyncio
async def test_find_free_slots_tool_invalid_duration():
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    now = datetime.utcnow()
    with pytest.raises(ValidationError):
        await find_free_slots_tool(FreeSlotsInput(
            provider="google",
            user_id=user_id,
            duration_minutes=-10,  # Invalid duration
            range_start=now,
            range_end=now + timedelta(hours=2)
        ))

@pytest.mark.asyncio
async def test_find_free_slots_tool_transient_error(mock_google_service):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Use AsyncMock for async methods
    mock_google_service.find_free_slots = AsyncMock(
        side_effect=[TimeoutError(), TimeoutError(), [{"start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(hours=1)}]]
    )
    now = datetime.utcnow()
    input_data = FreeSlotsInput(
        provider="google",
        user_id=user_id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(hours=2)
    )
    output = await find_free_slots_tool(input_data)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) > 0

@pytest.mark.asyncio
async def test_find_free_slots_tool_permanent_error(mocker, test_db, test_user):
    """Test find_free_slots_tool with a permanent error."""
    mocker.patch(
        "src.calendar_tool_wrappers.get_calendar_service",
        return_value=AsyncMock(
            find_free_slots=AsyncMock(side_effect=ValueError("Invalid range"))
        )
    )
    
    with pytest.raises(ToolExecutionError) as excinfo:
        await find_free_slots_tool(FreeSlotsInput(
            provider="google",
            user_id=str(test_user.id),
            range_start=datetime.utcnow(),
            range_end=datetime.utcnow() + timedelta(hours=5),
            duration_minutes=30
        ))
    
    assert "Failed to find free slots" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_event_tool_google_success(mock_google_service):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    now = datetime.utcnow()
    input_data = CreateEventInput(
        provider="google",
        user_id=user_id,
        summary="Test Event",
        start=now,
        end=now + timedelta(hours=1),
        attendees=[]
    )
    output = await create_event_tool(input_data)
    assert isinstance(output, CreateEventOutput)
    assert output.event.summary == "Test Event"
    assert output.event.id is not None

@pytest.mark.asyncio
async def test_create_event_tool_missing_required_fields():
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    now = datetime.utcnow()
    with pytest.raises(ValidationError):
        await create_event_tool(CreateEventInput(
            provider="google",
            user_id=user_id,
            # Missing summary
            start=now,
            end=now + timedelta(hours=1)
        ))

@pytest.mark.asyncio
async def test_create_event_tool_conflict(mocker, test_db, test_user):
    """Test create_event_tool with an event conflict error."""
    mocker.patch(
        "src.calendar_tool_wrappers.get_calendar_service",
        return_value=AsyncMock(
            create_event=AsyncMock(side_effect=HTTPException(status_code=409, detail="Event conflict"))
        )
    )
    
    with pytest.raises(ToolExecutionError) as excinfo:
        await create_event_tool(CreateEventInput(
            provider="google",
            user_id=str(test_user.id),
            summary="Test Event",
            start=datetime.utcnow().isoformat(),
            end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
        ))
    
    assert "Failed to create event" in str(excinfo.value)

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_reschedule_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_db: AsyncIOMotorDatabase
):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        microsoft_access_token="test_microsoft_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create an event in the database
    event = await create_event_in_db(test_db, user_id, provider_name, "Event to Reschedule")
    
    # New time for the event
    new_start = datetime.utcnow() + timedelta(days=1)
    new_end = new_start + timedelta(hours=1)
    
    input_data = RescheduleEventInput(
        provider=provider_name,
        user_id=user_id,
        event_id=str(event.id),
        new_start=new_start,
        new_end=new_end
    )
    
    output = await reschedule_event_tool(input_data)
    assert isinstance(output, RescheduleEventOutput)
    assert output.event is not None

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_cancel_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_db: AsyncIOMotorDatabase
):
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        google_access_token="test_google_token",
        microsoft_access_token="test_microsoft_token",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create an event in the database
    event = await create_event_in_db(test_db, user_id, provider_name, "Event to Cancel")
    
    input_data = CancelEventInput(
        provider=provider_name,
        user_id=user_id,
        event_id=str(event.id),
        start=datetime.utcnow(),
        end=datetime.utcnow() + timedelta(hours=1)
    )
    
    output = await cancel_event_tool(input_data)
    assert isinstance(output, CancelEventOutput)
    assert output.success is True

@pytest.fixture
def mock_get_user_by_id():
    """Mock for OAuthService.get_user_by_id method."""
    
    async def mock_get_user_by_id_impl(*args):
        # Extract user_id from args (could be called as method or function)
        # If called as a method: self, user_id = args
        # If called as a function: user_id = args[0]
        user_id = args[-1]  # Get the last argument which should be user_id
        
        # Create a proper User object with all required attributes
        from app.models.mongodb_models import User
        
        return User(
            id=user_id,
            email="test@example.com",
            name="Test User",
            google_access_token="test_google_token",
            microsoft_access_token="test_microsoft_token",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    return mock_get_user_by_id_impl

@pytest.fixture(autouse=True)
def patch_oauth_service(monkeypatch, mock_get_user_by_id):
    """Patch OAuthService for all tests."""
    from src.services.oauth_service import OAuthService
    monkeypatch.setattr(OAuthService, "get_user_by_id", mock_get_user_by_id)
    return mock_get_user_by_id

@pytest.fixture(autouse=True)
def mock_get_calendar_service_func(monkeypatch, mock_google_service, mock_microsoft_service):
    """Mock the get_calendar_service function."""
    
    async def mock_get_calendar_service_impl(provider, user_id):
        """Mock implementation of get_calendar_service."""
        if provider == "google":
            return mock_google_service
        elif provider == "microsoft":
            return mock_microsoft_service
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    # Patch the get_calendar_service function
    monkeypatch.setattr("src.calendar_tool_wrappers.get_calendar_service", mock_get_calendar_service_impl)
    
    return mock_get_calendar_service_impl 