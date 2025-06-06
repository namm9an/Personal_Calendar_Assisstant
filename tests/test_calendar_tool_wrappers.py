import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
import json
from uuid import UUID
from typing import Callable
from unittest.mock import patch, MagicMock, AsyncMock

from app.agent.calendar_tool_wrappers import (
    list_events_tool,
    find_free_slots_tool,
    create_event_tool,
    reschedule_event_tool,
    cancel_event_tool,
    _map_service_event_to_tool_event # Assuming _map is used internally or for verification
)
from app.schemas.tool_schemas import (
    ListEventsInput, ListEventsOutput,
    FreeSlotsInput, FreeSlotsOutput,
    CreateEventInput, CreateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput,
    EventSchema, AttendeeSchema # For constructing expected results
)
from app.core.exceptions import ToolExecutionError
from app.models import User
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, ANY # Added ANY

# Import conftest fixtures that are used implicitly or for type hinting
from .conftest import test_user, mock_google_service, mock_microsoft_service, BASE_DATETIME, TEST_USER_ID
# Import EventCreate for type checking arguments to mock service
from app.schemas.calendar import EventCreate, TimeSlot, EventAttendee, EventStatus

# Define providers list directly in the test file
PROVIDERS = ["google", "microsoft"]

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_list_events_tool_happy_path(
    provider_name: str, 
    db_session: Session, 
    test_user: User, 
    mock_google_service, # Fixture is active based on patch in conftest
    mock_microsoft_service # Fixture is active based on patch in conftest
):
    """Test list_events_tool happy path for both Google and Microsoft providers."""
    start_time = BASE_DATETIME - timedelta(days=1)
    end_time = BASE_DATETIME + timedelta(days=5)
    calendar_id = "primary"
    max_results = 5

    # Act
    result = await list_events_tool(
        ListEventsInput(
            provider=provider_name,
            user_id=str(test_user.id),
            start_time=start_time,
            end_time=end_time,
            calendar_id=calendar_id,
            max_results=max_results
        )
    )

    # Assert
    assert isinstance(result, ListEventsOutput)
    assert result["provider"] == provider_name
    assert result["calendar_id"] == calendar_id
    assert result["start_time"] == start_time.isoformat()
    assert result["end_time"] == end_time.isoformat()

    expected_events = []
    if provider_name == "google":
        # Based on MockGoogleService.get_events and _map_service_event_to_tool_event
        mock_raw_events = [
            {
                "id": "google_event_1", "summary": "Google Event 1",
                "start": {"dateTime": (BASE_DATETIME + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (BASE_DATETIME + timedelta(hours=2)).isoformat()},
                "description": "Google event 1 description",
                "location": "Google event 1 location",
                "attendees": [{"email": "att1@example.com", "name": "Attendee 1"}],
                "html_link": "link_to_google_event_1"
            },
            {
                "id": "google_event_2", "summary": "Google Event 2",
                "start": {"dateTime": (BASE_DATETIME + timedelta(days=1, hours=1)).isoformat()},
                "end": {"dateTime": (BASE_DATETIME + timedelta(days=1, hours=2)).isoformat()},
                "description": "Google event 2 description",
                "location": "Google event 2 location",
                "attendees": [],
                "html_link": "link_to_google_event_2"
            }
        ]
        for raw_event in mock_raw_events:
            # Manually map to compare with the tool's output which uses EventSchema(...).dict()
            mapped_event = EventSchema(
                id=raw_event["id"],
                summary=raw_event["summary"],
                start=datetime.fromisoformat(raw_event["start"]["dateTime"]),
                end=datetime.fromisoformat(raw_event["end"]["dateTime"]),
                description=raw_event["description"],
                location=raw_event["location"],
                attendees=[AttendeeSchema(**att) for att in raw_event["attendees"]],
                html_link=raw_event["html_link"]
            )
            expected_events.append(mapped_event.model_dump(mode='json')) # Pydantic v2 uses model_dump
        assert result["count"] == 2

    elif provider_name == "microsoft":
        mock_raw_events = [
            {
                "id": "ms_event_1", "summary": "Microsoft Event 1",
                "start": {"dateTime": (BASE_DATETIME + timedelta(hours=1)).isoformat()},
                "end": {"dateTime": (BASE_DATETIME + timedelta(hours=2)).isoformat()},
                "description": "Microsoft event 1 description",
                "location": "Microsoft event 1 location",
                "attendees": [{"email": "att_ms1@example.com", "name": "MS Attendee 1"}],
                "html_link": "link_to_ms_event_1"
            }
        ]
        for raw_event in mock_raw_events:
            mapped_event = EventSchema(
                id=raw_event["id"],
                summary=raw_event["summary"],
                start=datetime.fromisoformat(raw_event["start"]["dateTime"]),
                end=datetime.fromisoformat(raw_event["end"]["dateTime"]),
                description=raw_event["description"],
                location=raw_event["location"],
                attendees=[AttendeeSchema(**att) for att in raw_event["attendees"]],
                html_link=raw_event["html_link"]
            )
            expected_events.append(mapped_event.model_dump(mode='json'))
        assert result["count"] == 1
    
    # Deep comparison of event lists
    # Sort by id to ensure order doesn't affect comparison if events are not ordered by the tool
    assert sorted(result["events"], key=lambda x: x['id']) == sorted(expected_events, key=lambda x: x['id'])

    # Verify that the correct service was called (optional, but good for sanity)
    # The mock_google_service and mock_microsoft_service fixtures yield the patch object.
    # We need to access the mock instance created by the side_effect.
    # This part is tricky because the service is instantiated inside list_events_tool.
    # A more robust way would be to have the mock service instances record calls.

    # For now, the primary assertion is on the output based on the mock data.
    # If the output is correct, the correct mock service must have been used.

@pytest.mark.asyncio
async def test_list_events_tool_google_success(mock_google_service, test_user):
    now = datetime.utcnow()
    input = ListEventsInput(
        provider="google",
        user_id=test_user.id,
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    output = await list_events_tool(input)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 2
    assert all(isinstance(ev, EventSchema) for ev in output.events)

@pytest.mark.asyncio
async def test_list_events_tool_google_missing_credentials(test_user, db_session):
    # Modify test_user to have no Google credentials
    test_user.google_access_token = None
    db_session.commit()
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=test_user.id,
            start_time=now,
            end_time=now + timedelta(hours=1)
        ))
    assert "No Google credentials" in str(excinfo.value)

@pytest.mark.asyncio
async def test_list_events_tool_microsoft_success(mock_microsoft_service, test_user):
    now = datetime.utcnow()
    input = ListEventsInput(
        provider="microsoft",
        user_id=test_user.id,
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    output = await list_events_tool(input)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 1
    assert all(isinstance(ev, EventSchema) for ev in output.events)

@pytest.mark.asyncio
async def test_list_events_tool_transient_error(mock_google_service, test_user):
    # Simulate transient error (e.g., Timeout) on first two calls, then success
    mock_google_service.list_events.side_effect = [TimeoutError(), TimeoutError(), [{"id": "1", "summary": "Test Event", "start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(hours=1)}]]
    now = datetime.utcnow()
    input = ListEventsInput(
        provider="google",
        user_id=test_user.id,
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    output = await list_events_tool(input)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 1

@pytest.mark.asyncio
async def test_list_events_tool_permanent_error(mock_google_service, test_user):
    # Simulate permanent error
    mock_google_service.list_events.side_effect = ValueError("Invalid payload")
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await list_events_tool(ListEventsInput(
            provider="google",
            user_id=test_user.id,
            start_time=now,
            end_time=now + timedelta(hours=1)
        ))
    assert "Invalid payload" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_google_success(mock_google_service, test_user):
    now = datetime.utcnow()
    input = FreeSlotsInput(
        provider="google",
        user_id=test_user.id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(hours=2)
    )
    output = await find_free_slots_tool(input)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) > 0
    assert all(isinstance(slot, FreeSlotSchema) for slot in output.slots)

@pytest.mark.asyncio
async def test_find_free_slots_tool_microsoft_success(mock_microsoft_service, test_user):
    now = datetime.utcnow()
    input = FreeSlotsInput(
        provider="microsoft",
        user_id=test_user.id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(hours=2)
    )
    output = await find_free_slots_tool(input)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) > 0
    assert all(isinstance(slot, FreeSlotSchema) for slot in output.slots)

@pytest.mark.asyncio
async def test_find_free_slots_tool_invalid_duration(test_user):
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await find_free_slots_tool(FreeSlotsInput(
            provider="google",
            user_id=test_user.id,
            duration_minutes=0,
            range_start=now,
            range_end=now + timedelta(hours=2)
        ))
    assert "Duration must be positive" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_transient_error(mock_google_service, test_user):
    mock_google_service.find_free_slots.side_effect = [TimeoutError(), TimeoutError(), [{"start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(minutes=30)}]]
    now = datetime.utcnow()
    input = FreeSlotsInput(
        provider="google",
        user_id=test_user.id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(hours=2)
    )
    output = await find_free_slots_tool(input)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) == 1

@pytest.mark.asyncio
async def test_find_free_slots_tool_permanent_error(mock_google_service, test_user):
    mock_google_service.find_free_slots.side_effect = ValueError("Invalid payload")
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await find_free_slots_tool(FreeSlotsInput(
            provider="google",
            user_id=test_user.id,
            duration_minutes=30,
            range_start=now,
            range_end=now + timedelta(hours=2)
        ))
    assert "Invalid payload" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_event_tool_google_success(mock_google_service, test_user):
    now = datetime.utcnow()
    input = CreateEventInput(
        provider="google",
        user_id=test_user.id,
        summary="Test Event",
        start=now,
        end=now + timedelta(hours=1),
        description="Test Description",
        location="Test Location",
        attendees=[{"email": "test@example.com", "name": "Test User"}]
    )
    output = await create_event_tool(input)
    assert isinstance(output, CreateEventOutput)
    assert isinstance(output.event, EventSchema)
    assert output.event.summary == "Test Event"

@pytest.mark.asyncio
async def test_create_event_tool_missing_required_fields(test_user):
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await create_event_tool(CreateEventInput(
            provider="google",
            user_id=test_user.id,
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "Event summary is required" in str(excinfo.value)

@pytest.mark.asyncio
async def test_create_event_tool_conflict(mock_google_service, test_user):
    mock_google_service.create_event.side_effect = ValueError("Event conflicts with existing event")
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        await create_event_tool(CreateEventInput(
            provider="google",
            user_id=test_user.id,
            summary="Test Event",
            start=now,
            end=now + timedelta(hours=1)
        ))
    assert "Event conflicts with existing event" in str(excinfo.value)

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_reschedule_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session: Session
):
    now = datetime.utcnow()
    input = RescheduleEventInput(
        provider=provider_name,
        user_id=test_user.id,
        event_id="test_event_id",
        new_start=now + timedelta(hours=1),
        new_end=now + timedelta(hours=2)
    )
    output = await reschedule_event_tool(input)
    assert isinstance(output, RescheduleEventOutput)
    assert isinstance(output.event, EventSchema)
    assert output.event.id == "test_event_id"

@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", PROVIDERS)
async def test_cancel_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session: Session
):
    now = datetime.utcnow()
    input = CancelEventInput(
        provider=provider_name,
        user_id=test_user.id,
        event_id="test_event_id",
        start=now,
        end=now + timedelta(hours=1)
    )
    output = await cancel_event_tool(input)
    assert isinstance(output, CancelEventOutput)
    assert output.success is True
