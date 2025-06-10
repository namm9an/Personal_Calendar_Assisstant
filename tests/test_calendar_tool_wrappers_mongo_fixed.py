"""Tests for calendar tool wrappers with MongoDB."""
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

import pytest
from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError

from src.core.exceptions import ToolExecutionError
from app.models.mongodb_models import User, Event
from src.calendar_tool_wrappers import (
    list_events_tool,
    find_free_slots_tool,
    create_event_tool,
    reschedule_event_tool,
    cancel_event_tool,
    _map_service_event_to_tool_event,
    ListEventsInput, ListEventsOutput,
    FreeSlotsInput, FreeSlotsOutput, FreeSlotSchema,
    CreateEventInput, CreateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput,
    EventSchema, AttendeeSchema
)

# Define providers for parameterization
PROVIDERS = ["google", "microsoft"]

# Define a constant base datetime for consistent testing
BASE_DATETIME = datetime(2023, 1, 1, 12, 0, 0)

# Mock calendar service function
async def mock_get_calendar_service(provider: str, user_id: str):
    """Mock implementation of get_calendar_service function"""
    if provider == "google":
        from tests.conftest import MockGoogleService
        # Create a mock user object
        user = User(
            id=user_id,
            name="Test User",
            email="test@example.com",
            google_access_token="test_google_token",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create a wrapper around MockGoogleService to adapt its interface
        class GoogleServiceWrapper:
            def __init__(self):
                self._service = MockGoogleService(user, None)
                
            async def list_events(self, start_time=None, end_time=None, calendar_id="primary", max_results=10):
                return await self._service.list_events(time_min=start_time, time_max=end_time, calendar_id=calendar_id, max_results=max_results)
                
            async def find_free_slots(self, duration_minutes=30, range_start=None, range_end=None, calendar_id="primary"):
                return await self._service.find_free_slots(start_time=range_start, end_time=range_end, duration_minutes=duration_minutes, calendar_id=calendar_id)
                
            async def create_event(self, event_data, calendar_id="primary"):
                # Convert datetime objects to strings
                if isinstance(event_data.get('start'), dict) and isinstance(event_data['start'].get('dateTime'), datetime):
                    event_data['start']['dateTime'] = event_data['start']['dateTime'].isoformat()
                if isinstance(event_data.get('end'), dict) and isinstance(event_data['end'].get('dateTime'), datetime):
                    event_data['end']['dateTime'] = event_data['end']['dateTime'].isoformat()
                
                result = await self._service.create_event(event_data)
                
                # Handle nested dateTime format in results
                if isinstance(result.get('start', {}).get('dateTime'), dict):
                    result['start']['dateTime'] = result['start']['dateTime'].get('dateTime', '')
                if isinstance(result.get('end', {}).get('dateTime'), dict):
                    result['end']['dateTime'] = result['end']['dateTime'].get('dateTime', '')
                    
                return result
                
            async def update_event(self, event_id, event_data, calendar_id="primary"):
                return await self._service.update_event(event_id, event_data)
                
            async def reschedule_event(self, event_id, new_start, new_end, calendar_id="primary"):
                event_data = {
                    "summary": "Rescheduled Event",  # Add summary for Google
                    "subject": "Rescheduled Event",  # Add subject for Microsoft
                    "start": new_start.isoformat() if isinstance(new_start, datetime) else new_start,
                    "end": new_end.isoformat() if isinstance(new_end, datetime) else new_end
                }
                result = await self._service.update_event(event_id, event_data)
                
                # Handle nested dateTime format in results
                if isinstance(result.get('start', {}).get('dateTime'), dict):
                    result['start']['dateTime'] = result['start']['dateTime'].get('dateTime', '')
                if isinstance(result.get('end', {}).get('dateTime'), dict):
                    result['end']['dateTime'] = result['end']['dateTime'].get('dateTime', '')
                    
                return result
                
            async def cancel_event(self, event_id, start=None, end=None, calendar_id="primary"):
                return await self._service.delete_event(event_id)
                
        return GoogleServiceWrapper()
    elif provider == "microsoft":
        from tests.conftest import MockMicrosoftService
        
        # Create a wrapper around MockMicrosoftService to adapt its interface
        class MicrosoftServiceWrapper:
            def __init__(self):
                # MockMicrosoftService requires credentials, not a user object
                self._service = MockMicrosoftService("test_ms_credentials")
                
            async def list_events(self, start_time=None, end_time=None, calendar_id="primary", max_results=10):
                return await self._service.list_events(time_min=start_time, time_max=end_time, calendar_id=calendar_id, max_results=max_results)
                
            async def find_free_slots(self, duration_minutes=30, range_start=None, range_end=None, calendar_id="primary"):
                return await self._service.find_free_slots(start_time=range_start, end_time=range_end, duration_minutes=duration_minutes, calendar_id=calendar_id)
                
            async def create_event(self, event_data, calendar_id="primary"):
                # Convert datetime objects to strings
                if isinstance(event_data.get('start'), dict) and isinstance(event_data['start'].get('dateTime'), datetime):
                    event_data['start']['dateTime'] = event_data['start']['dateTime'].isoformat()
                if isinstance(event_data.get('end'), dict) and isinstance(event_data['end'].get('dateTime'), datetime):
                    event_data['end']['dateTime'] = event_data['end']['dateTime'].isoformat()
                    
                # Rename the field if needed - MS expects 'subject' instead of 'summary'
                if 'summary' in event_data and 'subject' not in event_data:
                    event_data['subject'] = event_data.pop('summary')
                
                result = await self._service.create_event(event_data)
                
                # Handle nested dateTime format in results
                if isinstance(result.get('start', {}).get('dateTime'), dict):
                    result['start']['dateTime'] = result['start']['dateTime'].get('dateTime', '')
                if isinstance(result.get('end', {}).get('dateTime'), dict):
                    result['end']['dateTime'] = result['end']['dateTime'].get('dateTime', '')
                    
                return result
                
            async def update_event(self, event_id, event_data, calendar_id="primary"):
                return await self._service.update_event(event_id, event_data)
                
            async def reschedule_event(self, event_id, new_start, new_end, calendar_id="primary"):
                event_data = {
                    "summary": "Rescheduled Event",  # Add summary for Google
                    "subject": "Rescheduled Event",  # Add subject for Microsoft
                    "start": new_start.isoformat() if isinstance(new_start, datetime) else new_start,
                    "end": new_end.isoformat() if isinstance(new_end, datetime) else new_end
                }
                result = await self._service.update_event(event_id, event_data)
                
                # Handle nested dateTime format in results
                if isinstance(result.get('start', {}).get('dateTime'), dict):
                    result['start']['dateTime'] = result['start']['dateTime'].get('dateTime', '')
                if isinstance(result.get('end', {}).get('dateTime'), dict):
                    result['end']['dateTime'] = result['end']['dateTime'].get('dateTime', '')
                    
                return result
                
            async def cancel_event(self, event_id, start=None, end=None, calendar_id="primary"):
                return await self._service.delete_event(event_id)
                
        return MicrosoftServiceWrapper()
    else:
        raise ValueError(f"Unsupported provider: {provider}")

# Patch the get_calendar_service function globally for all tests
@pytest.fixture(autouse=True)
def patch_get_calendar_service():
    with patch("src.calendar_tool_wrappers.get_calendar_service", side_effect=mock_get_calendar_service):
        yield

async def create_event_in_db(db: AsyncIOMotorDatabase, user_id: str, provider: str, summary: str) -> Event:
    """Create an event in the database for testing."""
    event_id = str(ObjectId())
    provider_event_id = f"test-event-{event_id}"
    
    # Current time
    now = datetime.utcnow()
    
    event_data = {
        "_id": event_id,
        "user_id": user_id,
        "summary": summary,
        "description": "Test event",
        "start_datetime": now,
        "end_datetime": now + timedelta(hours=1),
        "timezone": "UTC",
        "location": "Test location",
        "provider": provider,
        "provider_event_id": provider_event_id,
        "created_by": "test@example.com",
        "created_at": now,
        "updated_at": now
    }
    
    # Insert into database
    await db.events.insert_one({
        "_id": ObjectId(event_id),
        "user_id": user_id,
        "summary": summary,
        "description": "Test event",
        "start_datetime": now,
        "end_datetime": now + timedelta(hours=1),
        "timezone": "UTC",
        "location": "Test location",
        "provider": provider,
        "provider_event_id": provider_event_id,
        "created_by": "test@example.com",
        "created_at": now,
        "updated_at": now
    })
    
    return Event(**event_data)

async def get_event_from_db(db: AsyncIOMotorDatabase, event_id: str) -> Event:
    """Get an event from the database by ID."""
    event_data = await db.events.find_one({"_id": ObjectId(event_id)})
    if event_data:
        event_data["_id"] = str(event_data["_id"])
        return Event(**event_data)
    return None

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
        # Accept both test-generated events and mock service events
        if provider_name == "google":
            assert event.summary in ["Test Event 1", "Test Event 2", "Mock Google Event", "Another Mock Event", "Mock Event"]
        else:
            assert event.summary in ["Test Event 1", "Test Event 2", "Mock MS Event", "Mock Event"]

@pytest.mark.asyncio
async def test_list_events_tool_invalid_provider():
    """Test list_events_tool with an invalid provider."""
    now = datetime.utcnow()
    # We shouldn't use ValidationError here because the tool itself raises ToolExecutionError
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="invalid_provider",
            user_id=str(ObjectId()),
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "Unsupported provider" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_user_not_found(test_db: AsyncIOMotorDatabase):
    """Test list_events_tool with a non-existent user."""
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=str(ObjectId()),  # Generate a random ObjectId that doesn't exist
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "Failed to list events" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_google_missing_credentials(test_db: AsyncIOMotorDatabase):
    """Test list_events_tool with missing Google credentials."""
    # Create a user with no Google credentials
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "timezone": "UTC",
        "working_hours_start": "09:00",
        "working_hours_end": "17:00",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    result = await test_db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=user_id,
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "Failed to list events" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_microsoft_success(mock_microsoft_service):
    """Test list_events_tool with Microsoft provider."""
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
    input_data = ListEventsInput(
        provider="microsoft",
        user_id=user_id,
        start=now,
        end=now + timedelta(hours=1),
    )
    output = await list_events_tool(input_data)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 1
    assert all(isinstance(ev, EventSchema) for ev in output.events)

@pytest.mark.asyncio
async def test_list_events_tool_transient_error():
    """Test list_events_tool with transient errors."""
    user_id = str(ObjectId())
    now = datetime.utcnow()
    
    # Setup a mock service that raises TimeoutError
    with patch("src.calendar_tool_wrappers.get_calendar_service") as mock_get_service:
        # Create a mock service that raises TimeoutError
        mock_service = AsyncMock()
        mock_service.list_events = AsyncMock(side_effect=TimeoutError("Connection timeout"))
        mock_get_service.return_value = mock_service
        
        # Call the tool and expect a ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await list_events_tool(ListEventsInput(
                provider="google",
                user_id=user_id,
                start=now,
                end=now + timedelta(hours=1),
            ))
        
        assert "Failed to list events" in str(excinfo.value) or "timed out" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_permanent_error():
    """Test list_events_tool with permanent errors."""
    user_id = str(ObjectId())
    now = datetime.utcnow()
    
    # Setup a mock service that raises ValueError
    with patch("src.calendar_tool_wrappers.get_calendar_service") as mock_get_service:
        # Create a mock service that raises ValueError
        mock_service = AsyncMock()
        mock_service.list_events = AsyncMock(side_effect=ValueError("Invalid payload"))
        mock_get_service.return_value = mock_service
        
        # Call the tool and expect a ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await list_events_tool(ListEventsInput(
                provider="google",
                user_id=user_id,
                start=now,
                end=now + timedelta(hours=1),
            ))
        
        assert "Invalid payload" in str(excinfo.value) or "Failed to list events" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_google_success(mock_google_service):
    """Test find_free_slots_tool with Google provider."""
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
    """Test find_free_slots_tool with Microsoft provider."""
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
    """Test find_free_slots_tool with invalid duration."""
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
    # Should raise a ToolExecutionError instead of ValidationError
    with pytest.raises(ToolExecutionError) as excinfo:
        await find_free_slots_tool(FreeSlotsInput(
            provider="google",
            user_id=user_id,
            duration_minutes=-10,  # Invalid duration
            range_start=now,
            range_end=now + timedelta(hours=2)
        ))
    assert "Duration must be positive" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_transient_error():
    """Test find_free_slots_tool with transient errors."""
    user_id = str(ObjectId())
    now = datetime.utcnow()
    
    # Setup a mock service that raises TimeoutError
    with patch("src.calendar_tool_wrappers.get_calendar_service") as mock_get_service:
        # Create a mock service that raises TimeoutError
        mock_service = AsyncMock()
        mock_service.find_free_slots = AsyncMock(side_effect=TimeoutError("Connection timeout"))
        mock_get_service.return_value = mock_service
        
        # Call the tool and expect a ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await find_free_slots_tool(FreeSlotsInput(
                provider="google",
                user_id=user_id,
                duration_minutes=30,
                range_start=now,
                range_end=now + timedelta(hours=2)
            ))
        
        assert "Failed to find free slots" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_permanent_error():
    """Test find_free_slots_tool with permanent errors."""
    user_id = str(ObjectId())
    now = datetime.utcnow()
    
    # Setup a mock service that raises ValueError
    with patch("src.calendar_tool_wrappers.get_calendar_service") as mock_get_service:
        # Create a mock service that raises ValueError
        mock_service = AsyncMock()
        mock_service.find_free_slots = AsyncMock(side_effect=ValueError("Invalid range"))
        mock_get_service.return_value = mock_service
        
        # Call the tool and expect a ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await find_free_slots_tool(FreeSlotsInput(
                provider="google",
                user_id=user_id,
                duration_minutes=30,
                range_start=now,
                range_end=now + timedelta(hours=2)
            ))
        
        assert "Failed to find free slots" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_event_tool_google_success(mock_google_service):
    """Test create_event_tool with Google provider."""
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
    assert isinstance(output.event, EventSchema)
    assert output.event.summary == "Test Event" or output.event.summary == "mock_google_event_2"

@pytest.mark.asyncio
async def test_create_event_tool_missing_required_fields():
    """Test create_event_tool with missing required fields."""
    # Create a non-coroutine user object for testing
    user_id = str(ObjectId())
    now = datetime.utcnow()
    
    # Should raise a ToolExecutionError for missing summary
    with pytest.raises(ToolExecutionError) as excinfo:
        await create_event_tool(CreateEventInput(
            provider="google",
            user_id=user_id,
            summary="",  # Empty summary
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "summary is required" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_event_tool_conflict():
    """Test create_event_tool with event conflicts."""
    user_id = str(ObjectId())
    now = datetime.utcnow()
    
    # Setup a mock service that raises HTTPException with 409 status
    with patch("src.calendar_tool_wrappers.get_calendar_service") as mock_get_service:
        # Create a mock service that raises HTTPException
        mock_service = AsyncMock()
        mock_service.create_event = AsyncMock(
            side_effect=HTTPException(status_code=409, detail="Event conflicts with existing event")
        )
        mock_get_service.return_value = mock_service
        
        # Call the tool and expect a ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await create_event_tool(CreateEventInput(
                provider="google",
                user_id=user_id,
                summary="Conflicting Event",
                start=now,
                end=now + timedelta(hours=1)
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
    """Test reschedule_event_tool with both providers."""
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
    
    # Create a test event in the database
    event = await create_event_in_db(test_db, user_id, provider_name, "Test Event")
    
    # Reschedule the event
    now = datetime.utcnow()
    input_data = RescheduleEventInput(
        provider=provider_name,
        user_id=user_id,
        event_id=event.provider_event_id if hasattr(event, 'provider_event_id') else event.id,
        new_start=now + timedelta(hours=2),
        new_end=now + timedelta(hours=3),
        calendar_id="primary"
    )
    
    output = await reschedule_event_tool(input_data)
    assert isinstance(output, RescheduleEventOutput)
    assert isinstance(output.event, EventSchema)

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_cancel_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_db: AsyncIOMotorDatabase
):
    """Test cancel_event_tool with both providers."""
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
    
    # Create a test event in the database
    event = await create_event_in_db(test_db, user_id, provider_name, "Test Event")
    
    # Get the current time for start/end
    now = datetime.utcnow()
    
    # Cancel the event
    input_data = CancelEventInput(
        provider=provider_name,
        user_id=user_id,
        event_id=event.provider_event_id if hasattr(event, 'provider_event_id') else event.id,
        start=now,
        end=now + timedelta(hours=1),
        calendar_id="primary"
    )
    
    output = await cancel_event_tool(input_data)
    assert isinstance(output, CancelEventOutput)
    assert output.success is True 