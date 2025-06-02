import pytest
from datetime import datetime, timedelta, timezone
import json
from uuid import UUID

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
from .conftest import db_session, test_user, mock_google_service, mock_microsoft_service, providers, BASE_DATETIME, TEST_USER_ID
# Import EventCreate for type checking arguments to mock service
from app.schemas.calendar import EventCreate, EventTimeSlot, Attendee, EventStatus

@pytest.mark.parametrize("provider_name", providers)
def test_list_events_tool_happy_path(
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
    result = list_events_tool(
        db=db_session,
        provider=provider_name,
        user_id=str(test_user.id),
        start_time=start_time,
        end_time=end_time,
        calendar_id=calendar_id,
        max_results=max_results
    )

    # Assert
    assert isinstance(result, dict)
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

def test_list_events_tool_google_success(mock_google_service, test_user):
    now = datetime.utcnow()
    input = ListEventsInput(
        provider="google",
        user_id=test_user.id,
        start=now,
        end=now + timedelta(hours=1),
    )
    output = list_events_tool(input)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 2
    assert all(isinstance(ev, EventSchema) for ev in output.events)

def test_list_events_tool_google_missing_credentials(test_user, db_session):
    # Modify test_user to have no Google credentials
    test_user.google_access_token = None
    db_session.commit()
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        list_events_tool(ListEventsInput("google", test_user.id, now, now + timedelta(hours=1)))
    assert "No Google credentials" in str(excinfo.value)

def test_list_events_tool_microsoft_success(mock_microsoft_service, test_user):
    now = datetime.utcnow()
    input = ListEventsInput(
        provider="microsoft",
        user_id=test_user.id,
        start=now,
        end=now + timedelta(hours=1),
    )
    output = list_events_tool(input)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 1
    assert all(isinstance(ev, EventSchema) for ev in output.events)

def test_list_events_tool_transient_error(mock_google_service, test_user):
    # Simulate transient error (e.g., Timeout) on first two calls, then success
    mock_google_service.list_events.side_effect = [TimeoutError(), TimeoutError(), [{"id": "1", "summary": "Test Event", "start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(hours=1)}]]
    now = datetime.utcnow()
    input = ListEventsInput(
        provider="google",
        user_id=test_user.id,
        start=now,
        end=now + timedelta(hours=1),
    )
    output = list_events_tool(input)
    assert isinstance(output, ListEventsOutput)
    assert len(output.events) == 1

def test_list_events_tool_permanent_error(mock_google_service, test_user):
    # Simulate permanent error
    mock_google_service.list_events.side_effect = ValueError("Invalid payload")
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        list_events_tool(ListEventsInput("google", test_user.id, now, now + timedelta(hours=1)))
    assert "Invalid payload" in str(excinfo.value)

def test_find_free_slots_tool_google_success(mock_google_service, test_user):
    now = datetime.utcnow()
    input = FreeSlotsInput(
        provider="google",
        user_id=test_user.id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(days=1),
    )
    output = find_free_slots_tool(input)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) == 2

def test_find_free_slots_tool_microsoft_success(mock_microsoft_service, test_user):
    now = datetime.utcnow()
    input = FreeSlotsInput(
        provider="microsoft",
        user_id=test_user.id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(days=1),
    )
    output = find_free_slots_tool(input)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) == 1

def test_find_free_slots_tool_invalid_duration(test_user):
    now = datetime.utcnow()
    with pytest.raises(ValueError):
        FreeSlotsInput(
            provider="google",
            user_id=test_user.id,
            duration_minutes=-10,
            range_start=now,
            range_end=now + timedelta(days=1),
        )

def test_find_free_slots_tool_transient_error(mock_google_service, test_user):
    mock_google_service.find_free_slots.side_effect = [TimeoutError(), TimeoutError(), [{"start": datetime.utcnow(), "end": datetime.utcnow() + timedelta(minutes=30)}]]
    now = datetime.utcnow()
    input = FreeSlotsInput(
        provider="google",
        user_id=test_user.id,
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(days=1),
    )
    output = find_free_slots_tool(input)
    assert isinstance(output, FreeSlotsOutput)
    assert len(output.slots) == 1

def test_find_free_slots_tool_permanent_error(mock_google_service, test_user):
    mock_google_service.find_free_slots.side_effect = ValueError("Invalid payload")
    now = datetime.utcnow()
    with pytest.raises(ToolExecutionError) as excinfo:
        find_free_slots_tool(FreeSlotsInput("google", test_user.id, 30, now, now + timedelta(days=1)))
    assert "Invalid payload" in str(excinfo.value)

def test_create_event_tool_google_success(mock_google_service, test_user):
    now = datetime.utcnow()
    input = CreateEventInput(
        provider="google",
        user_id=test_user.id,
        summary="Team Meeting",
        start=now + timedelta(hours=2),
        end=now + timedelta(hours=3),
        description="Discuss Q2 goals",
        location="Conference Room A",
        attendees=[{"email": "alice@example.com"}],
    )
    output = create_event_tool(input)
    assert isinstance(output, CreateEventOutput)
    assert isinstance(output.event, EventSchema)

def test_create_event_tool_missing_required_fields(test_user):
    now = datetime.utcnow()
    with pytest.raises(ValueError):
        CreateEventInput(
            provider="google",
            user_id=test_user.id,
            start=now + timedelta(hours=2),
            end=now + timedelta(hours=3),
        )

def test_create_event_tool_conflict(mock_google_service, test_user):
    mock_google_service.create_event.side_effect = Exception("Time slot unavailable")
    now = datetime.utcnow()
    input = CreateEventInput(
        provider="google",
        user_id=test_user.id,
        summary="Team Meeting",
        start=now + timedelta(hours=2),
        end=now + timedelta(hours=3),
    )
    with pytest.raises(ToolExecutionError) as excinfo:
        create_event_tool(input)
    assert "Time slot unavailable" in str(excinfo.value)

@pytest.mark.parametrize("provider_name", providers)
def test_reschedule_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session: Session,
    db_session_factory: Callable[[], Session]
):
    """Test reschedule_event_tool happy path for both Google and Microsoft providers."""
    original_event_id = f"{provider_name}_event_to_reschedule"
    calendar_id = "primary"
    now = datetime.now(timezone.utc)
    new_start_dt = now + timedelta(days=2)
    new_end_dt = new_start_dt + timedelta(hours=1)
    new_time_zone = "America/New_York"

    input_data = RescheduleEventInput(
        provider_name=provider_name,
        event_id=original_event_id,
        new_start_datetime=new_start_dt,
        new_end_datetime=new_end_dt,
        calendar_id=calendar_id,
        new_time_zone=new_time_zone
    )

    expected_summary = f"Rescheduled {provider_name.capitalize()} Event"
    expected_description = "Successfully rescheduled."
    expected_location = "New Location"

    # This is the dictionary that the mock service's update_event should return
    mock_service_response = {
        "id": original_event_id,
        "summary": expected_summary,
        "description": expected_description,
        "location": expected_location,
        "start": {"dateTime": new_start_dt.isoformat(), "timeZone": new_time_zone},
        "end": {"dateTime": new_end_dt.isoformat(), "timeZone": new_time_zone},
        "attendees": [{"email": "attendee@example.com", "responseStatus": "accepted"}],
        "htmlLink": f"http://mock.calendar.com/{provider_name}/{original_event_id}",
        "status": EventStatus.CONFIRMED.value,
        "calendarId": calendar_id
    }

    active_mock_service = mock_google_service if provider_name == "google" else mock_microsoft_service
    active_mock_service.update_event = MagicMock(return_value=mock_service_response)

    # --- Test Case 1: Calling with user_id and db_session_factory --- 
    result_factory_call = reschedule_event_tool(
        user_id=str(test_user.id),
        input_data=input_data,
        db_session_factory=db_session_factory
    )

    assert isinstance(result_factory_call, RescheduleEventOutput)
    assert result_factory_call.event.id == original_event_id
    assert result_factory_call.event.summary == expected_summary
    assert result_factory_call.event.description == expected_description
    assert result_factory_call.event.location == expected_location
    assert result_factory_call.event.start_time == new_start_dt
    assert result_factory_call.event.end_time == new_end_dt
    assert result_factory_call.event.time_zone == new_time_zone
    assert len(result_factory_call.event.attendees) == 1
    assert result_factory_call.event.attendees[0].email == "attendee@example.com"
    assert result_factory_call.event.html_link == f"http://mock.calendar.com/{provider_name}/{original_event_id}"
    assert result_factory_call.event.status == EventStatus.CONFIRMED.value

    expected_event_update_payload = EventUpdate(
        time_slot=ServiceTimeSlot(start=new_start_dt, end=new_end_dt)
        # new_time_zone is handled by the service/CalendarTools, not directly in EventUpdate model for this wrapper
    )
    active_mock_service.update_event.assert_called_once_with(
        event_id=original_event_id,
        calendar_id=calendar_id,
        event_update=ANY # Using ANY because EventUpdate equality can be tricky with optional fields
        # We can be more specific if needed by comparing fields of the ANY object 
        # or by constructing the exact EventUpdate object passed.
    )
    # More precise check for EventUpdate payload:
    args, kwargs = active_mock_service.update_event.call_args
    actual_event_update: EventUpdate = kwargs.get('event_update') or (args[2] if len(args) > 2 else None)
    assert isinstance(actual_event_update, EventUpdate)
    assert actual_event_update.time_slot.start == new_start_dt
    assert actual_event_update.time_slot.end == new_end_dt
    # Reset mock for the next call pattern
    active_mock_service.update_event.reset_mock()

    # --- Test Case 2: Calling with pre-initialized CalendarTools instance --- 
    calendar_tools_instance = CalendarTools(user=test_user, db_session=db_session, provider_name=provider_name)
    # Spy on the instance's reschedule_event method if needed, but here we rely on the underlying service mock
    # calendar_tools_instance.calendar_service.update_event = MagicMock(return_value=mock_service_response) # Already configured on active_mock_service which is what this instance will use

    result_instance_call = reschedule_event_tool(
        calendar_tools_instance=calendar_tools_instance,
        input_data=input_data,
        user_id=str(test_user.id) # Optional, but good to test consistency check
    )

    assert isinstance(result_instance_call, RescheduleEventOutput)
    assert result_instance_call.event.id == original_event_id
    assert result_instance_call.event.summary == expected_summary 
    # ... (repeat assertions for other fields as above) ...
    assert result_instance_call.event.start_time == new_start_dt
    assert result_instance_call.event.end_time == new_end_dt
    assert result_instance_call.event.time_zone == new_time_zone

    active_mock_service.update_event.assert_called_once()
    args_instance, kwargs_instance = active_mock_service.update_event.call_args
    actual_event_update_instance: EventUpdate = kwargs_instance.get('event_update') or (args_instance[2] if len(args_instance) > 2 else None)
    assert isinstance(actual_event_update_instance, EventUpdate)
    assert actual_event_update_instance.time_slot.start == new_start_dt
    assert actual_event_update_instance.time_slot.end == new_end_dt

@pytest.mark.parametrize("provider_name", providers)
def test_reschedule_event_tool_event_not_found(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test reschedule_event_tool when the event is not found (404)."""
    event_id_not_found = "non_existent_event_id"
    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name=provider_name,
        event_id=event_id_not_found,
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1),
        calendar_id="primary"
    )

    active_mock_service = mock_google_service if provider_name == "google" else mock_microsoft_service

    if provider_name == "google":
        # Simulate GoogleHttpError for 404
        # The mock service in conftest.py should raise this if event_id is 'google_event_404_not_found'
        # For a generic test, we set side_effect here.
        google_error_response = MagicMock()
        google_error_response.status = 404
        active_mock_service.update_event = MagicMock(side_effect=GoogleHttpError(resp=google_error_response, content=b'Event not found'))
    else: # microsoft
        # Simulate HTTPException for 404
        # The mock service in conftest.py should raise this if event_id is 'ms_event_404_not_found'
        active_mock_service.update_event = MagicMock(side_effect=HTTPException(status_code=404, detail="Event not found"))

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    
    assert "not found" in str(excinfo.value).lower()
    if provider_name == "google":
        assert isinstance(excinfo.value.original_exception, GoogleHttpError)
    else:
        assert isinstance(excinfo.value.original_exception, HTTPException)
    active_mock_service.update_event.assert_called_once()

@pytest.mark.parametrize("provider_name", providers)
def test_reschedule_event_tool_auth_failure(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test reschedule_event_tool with authentication failure (401)."""
    event_id = "any_event_id"
    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name=provider_name,
        event_id=event_id,
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1),
        calendar_id="primary"
    )

    active_mock_service = mock_google_service if provider_name == "google" else mock_microsoft_service

    if provider_name == "google":
        google_error_response = MagicMock()
        google_error_response.status = 401
        active_mock_service.update_event = MagicMock(side_effect=GoogleHttpError(resp=google_error_response, content=b'Unauthorized'))
    else: # microsoft
        active_mock_service.update_event = MagicMock(side_effect=HTTPException(status_code=401, detail="Unauthorized"))

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    
    assert "unauthorized" in str(excinfo.value).lower() or "authentication" in str(excinfo.value).lower()
    if provider_name == "google":
        assert isinstance(excinfo.value.original_exception, GoogleHttpError)
    else:
        assert isinstance(excinfo.value.original_exception, HTTPException)
    active_mock_service.update_event.assert_called_once()

def test_reschedule_event_tool_user_not_found(
    db_session_factory: Callable[[], Session],
    test_user: User # test_user fixture ensures a user exists, so we need to simulate non-existence
):
    """Test reschedule_event_tool when user_id does not correspond to an existing user."""
    non_existent_user_id = str(UUID("00000000-0000-0000-0000-000000000000"))
    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name="google", # Provider doesn't matter here
        event_id="any_event_id",
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1)
    )

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            user_id=non_existent_user_id,
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    assert f"User with ID '{non_existent_user_id}' not found" in str(excinfo.value)

def test_reschedule_event_tool_invalid_input_data_type(test_user: User, db_session_factory: Callable[[], Session]):
    """Test reschedule_event_tool with invalid input_data type."""
    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            user_id=str(test_user.id),
            input_data=12345, # Invalid type
            db_session_factory=db_session_factory
        )
    assert "input_data must be a RescheduleEventInput model or a compatible dict" in str(excinfo.value)

def test_reschedule_event_tool_missing_tool_params(test_user: User):
    """Test reschedule_event_tool when neither instance nor factory params are provided."""
    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name="google",
        event_id="any_event_id",
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1)
    )
    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(input_data=input_data) # Missing user_id/db_session_factory and instance
    assert "Either calendar_tools_instance or (user_id and db_session_factory) must be provided" in str(excinfo.value)

def test_reschedule_event_tool_user_id_mismatch_with_instance(
    test_user: User, 
    db_session: Session, 
    mock_google_service: MagicMock
):
    """Test user_id mismatch when calendar_tools_instance is provided."""
    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name="google",
        event_id="any_event_id",
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1)
    )
    calendar_tools_instance = CalendarTools(user=test_user, db_session=db_session, provider_name="google")
    mismatched_user_id = str(UUID("11111111-1111-1111-1111-111111111111"))

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            calendar_tools_instance=calendar_tools_instance,
            input_data=input_data,
            user_id=mismatched_user_id
        )
    assert "Provided user_id does not match CalendarTools instance's user" in str(excinfo.value)

def test_reschedule_event_tool_provider_mismatch_with_instance(
    test_user: User, 
    db_session: Session, 
    mock_google_service: MagicMock # Mock service for the instance
):
    """Test provider_name mismatch when calendar_tools_instance is provided."""
    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name="microsoft", # Mismatched provider
        event_id="any_event_id",
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1)
    )
    # Instance is for Google
    calendar_tools_instance = CalendarTools(user=test_user, db_session=db_session, provider_name="google") 

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            calendar_tools_instance=calendar_tools_instance,
            input_data=input_data
        )
    assert "Input provider_name 'microsoft' does not match CalendarTools instance provider 'google'" in str(excinfo.value)

def test_reschedule_event_tool_invalid_input_schema(
    test_user: User, 
    db_session_factory: Callable[[], Session]
):
    """Test that Pydantic validation errors on RescheduleEventInput are wrapped."""
    now = datetime.now(timezone.utc)
    invalid_dict_input = {
        "provider_name": "google",
        "event_id": "some_id",
        "new_start_datetime": now,
        "new_end_datetime": now - timedelta(hours=1) # Invalid: end before start
    }
    with pytest.raises(ToolExecutionError) as excinfo: # Expecting wrapper to catch ValidationError from Pydantic
        reschedule_event_tool(
            user_id=str(test_user.id),
            input_data=invalid_dict_input,
            db_session_factory=db_session_factory
        )
    # The wrapper itself raises ToolExecutionError if input_data can't be parsed to RescheduleEventInput
    # Pydantic's ValidationError will be part of the cause if the dict structure is okay but values are bad.
    # The current wrapper code: `event_input_model = RescheduleEventInput(**input_data)` will raise Pydantic's ValidationError.
    # This will then be caught by the generic `except Exception as e:` and wrapped in ToolExecutionError.
    assert "An unexpected error occurred" in str(excinfo.value) # Default message for generic exception
    assert isinstance(excinfo.value.original_exception, ValidationError)

@pytest.mark.parametrize("provider_name", providers)
def test_cancel_event_tool_happy_path(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session: Session, # For CalendarTools instance
    db_session_factory: Callable[[], Session] # For factory call pattern
):
    """Test cancel_event_tool happy path for both Google and Microsoft providers."""
    event_id_to_cancel = f"{provider_name}_event_to_cancel"
    calendar_id = "primary"

    input_data = CancelEventInput(
        provider_name=provider_name,
        event_id=event_id_to_cancel,
        calendar_id=calendar_id
    )

    active_mock_service = mock_google_service if provider_name == "google" else mock_microsoft_service
    # Assuming CalendarTools.cancel_event calls service.delete_event
    # The service's delete_event method should return True for success as per current tool wrapper logic
    active_mock_service.delete_event = MagicMock(return_value=True) 

    # --- Test Case 1: Calling with user_id and db_session_factory --- 
    result_factory_call = cancel_event_tool(
        user_id=str(test_user.id),
        input_data=input_data,
        db_session_factory=db_session_factory
    )

    assert isinstance(result_factory_call, CancelEventOutput)
    assert result_factory_call.success is True
    assert result_factory_call.event_id == event_id_to_cancel
    assert result_factory_call.calendar_id == calendar_id
    assert result_factory_call.provider == provider_name

    active_mock_service.delete_event.assert_called_once_with(
        event_id=event_id_to_cancel,
        calendar_id=calendar_id
    )
    active_mock_service.delete_event.reset_mock()

    # --- Test Case 2: Calling with pre-initialized CalendarTools instance --- 
    calendar_tools_instance = CalendarTools(user=test_user, db_session=db_session, provider_name=provider_name)
    # Ensure the instance uses the correctly mocked service method
    # (already configured on active_mock_service which this instance will use)

    result_instance_call = cancel_event_tool(
        calendar_tools_instance=calendar_tools_instance,
        input_data=input_data,
        user_id=str(test_user.id) # Optional, for consistency check
    )

    assert isinstance(result_instance_call, CancelEventOutput)
    assert result_instance_call.success is True
    assert result_instance_call.event_id == event_id_to_cancel
    active_mock_service.delete_event.assert_called_once_with(
        event_id=event_id_to_cancel,
        calendar_id=calendar_id
    )


@pytest.mark.parametrize("provider_name", providers)
def test_cancel_event_tool_event_not_found(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test cancel_event_tool when the event is not found (service raises error)."""
    event_id_not_found = "non_existent_event_id"
    input_data = CancelEventInput(
        provider_name=provider_name,
        event_id=event_id_not_found,
        calendar_id="primary"
    )

    active_mock_service = mock_google_service if provider_name == "google" else mock_microsoft_service

    if provider_name == "google":
        google_error_response = MagicMock()
        google_error_response.status = 404
        active_mock_service.delete_event = MagicMock(side_effect=GoogleHttpError(resp=google_error_response, content=b'Event not found'))
    else: # microsoft
        active_mock_service.delete_event = MagicMock(side_effect=HTTPException(status_code=404, detail="Event not found"))

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    
    assert "not found" in str(excinfo.value).lower()
    if provider_name == "google":
        assert isinstance(excinfo.value.original_exception, GoogleHttpError)
    else:
        assert isinstance(excinfo.value.original_exception, HTTPException)
    active_mock_service.delete_event.assert_called_once()


@pytest.mark.parametrize("provider_name", providers)
def test_cancel_event_tool_auth_failure(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test cancel_event_tool with authentication failure (service raises error)."""
    event_id = "any_event_id"
    input_data = CancelEventInput(
        provider_name=provider_name,
        event_id=event_id,
        calendar_id="primary"
    )

    active_mock_service = mock_google_service if provider_name == "google" else mock_microsoft_service

    if provider_name == "google":
        google_error_response = MagicMock()
        google_error_response.status = 401
        active_mock_service.delete_event = MagicMock(side_effect=GoogleHttpError(resp=google_error_response, content=b'Unauthorized'))
    else: # microsoft
        active_mock_service.delete_event = MagicMock(side_effect=HTTPException(status_code=401, detail="Unauthorized"))

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    
    assert "unauthorized" in str(excinfo.value).lower() or "authentication" in str(excinfo.value).lower()
    if provider_name == "google":
        assert isinstance(excinfo.value.original_exception, GoogleHttpError)
    else:
        assert isinstance(excinfo.value.original_exception, HTTPException)
    active_mock_service.delete_event.assert_called_once()

def test_cancel_event_tool_user_not_found(
    db_session_factory: Callable[[], Session]
):
    """Test cancel_event_tool when user_id does not correspond to an existing user."""
    non_existent_user_id = str(UUID("00000000-0000-0000-0000-000000000000"))
    input_data = CancelEventInput(
        provider_name="google", 
        event_id="any_event_id"
    )

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=non_existent_user_id,
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    assert f"User with ID '{non_existent_user_id}' not found" in str(excinfo.value)


def test_cancel_event_tool_invalid_input_data_type(test_user: User, db_session_factory: Callable[[], Session]):
    """Test cancel_event_tool with invalid input_data type."""
    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=str(test_user.id),
            input_data=12345, # Invalid type
            db_session_factory=db_session_factory
        )
    assert "input_data must be a CancelEventInput model or a compatible dict" in str(excinfo.value)


def test_cancel_event_tool_missing_tool_params():
    """Test cancel_event_tool when neither instance nor factory params are provided."""
    input_data = CancelEventInput(provider_name="google", event_id="any_event_id")
    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(input_data=input_data) 
    assert "Either calendar_tools_instance or (user_id and db_session_factory) must be provided" in str(excinfo.value)


def test_cancel_event_tool_user_id_mismatch_with_instance(
    test_user: User, 
    db_session: Session
):
    """Test user_id mismatch when calendar_tools_instance is provided."""
    input_data = CancelEventInput(provider_name="google", event_id="any_event_id")
    calendar_tools_instance = CalendarTools(user=test_user, db_session=db_session, provider_name="google")
    mismatched_user_id = str(UUID("11111111-1111-1111-1111-111111111111"))

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            calendar_tools_instance=calendar_tools_instance,
            input_data=input_data,
            user_id=mismatched_user_id
        )
    assert "Provided user_id does not match CalendarTools instance's user" in str(excinfo.value)


def test_cancel_event_tool_provider_mismatch_with_instance(
    test_user: User, 
    db_session: Session
):
    """Test provider_name mismatch when calendar_tools_instance is provided."""
    input_data = CancelEventInput(provider_name="microsoft", event_id="any_event_id")
    calendar_tools_instance = CalendarTools(user=test_user, db_session=db_session, provider_name="google") 

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            calendar_tools_instance=calendar_tools_instance,
            input_data=input_data
        )
    assert "Input provider_name 'microsoft' does not match CalendarTools instance provider 'google'" in str(excinfo.value)


def test_cancel_event_tool_invalid_input_schema(
    test_user: User, 
    db_session_factory: Callable[[], Session]
):
    """Test that Pydantic validation errors on CancelEventInput are wrapped."""
    invalid_dict_input = {
        "provider_name": "google",
        # Missing event_id
    }
    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=str(test_user.id),
            input_data=invalid_dict_input,
            db_session_factory=db_session_factory
        )
    assert "An unexpected error occurred" in str(excinfo.value) 
    assert isinstance(excinfo.value.original_exception, ValidationError)


@patch('app.agent.tools.GoogleCalendarService')
def test_cancel_event_tool_google_service_init_failure(
    MockGoogleCalendarService: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test cancel_event_tool when GoogleCalendarService fails to initialize."""
    MockGoogleCalendarService.side_effect = TokenDecryptionError("Failed to decrypt token for cancel")
    input_data = CancelEventInput(provider_name="google", event_id="any_event_id")

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    assert "An unexpected error occurred" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, TokenDecryptionError)
    assert "Failed to decrypt token for cancel" in str(excinfo.value.original_exception)
    MockGoogleCalendarService.assert_called_once_with(user=test_user, db=ANY)


@patch('app.agent.tools.MicrosoftCalendarService')
def test_cancel_event_tool_microsoft_service_init_failure(
    MockMicrosoftCalendarService: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test cancel_event_tool when MicrosoftCalendarService fails to initialize."""
    MockMicrosoftCalendarService.side_effect = ConnectionError("MS Graph API connection failed for cancel")
    input_data = CancelEventInput(provider_name="microsoft", event_id="any_event_id")

    with pytest.raises(ToolExecutionError) as excinfo:
        cancel_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    assert "An unexpected error occurred" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, ConnectionError)
    assert "MS Graph API connection failed for cancel" in str(excinfo.value.original_exception)
    MockMicrosoftCalendarService.assert_called_once()


# The old test_cancel_event_tool_transient_error can be removed as its general case
# is covered by more specific error tests like auth_failure or a simulated 503 if needed.

from google.oauth2.credentials import Credentials as GoogleCredentials # Alias
from app.services.google_calendar import TokenRefreshException # Custom exception
from unittest.mock import MagicMock, Mock
from googleapiclient.errors import HttpError as GoogleHttpError

if 'BASE_DATETIME' not in globals():
    pass # Add pass to satisfy indentation requirement
    # ... (rest of the code remains the same)

@pytest.mark.parametrize("provider_name", providers)
def test_list_events_tool_api_error(
    db_session, test_user: User, 
    mock_google_service: Mock, 
    mock_microsoft_service: Mock, 
    provider_name, monkeypatch
):
    """
    Tests list_events_tool when the underlying service call (API call) fails.
    """
    start_time_dt = BASE_DATETIME
    end_time_dt = BASE_DATETIME + timedelta(days=1)

    # Ensure tokens are present for the initial part of the call
    test_user.google_access_token = "dummy_ciphertext_google_access_token"
    test_user.google_refresh_token = "dummy_ciphertext_google_refresh_token"
    test_user.microsoft_access_token = "dummy_ciphertext_microsoft_access_token"
    test_user.microsoft_refresh_token = "dummy_ciphertext_microsoft_refresh_token"
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    expected_internal_exception_type = None
    expected_error_message_part = ""

    if provider_name == "google":
        # The list_events_tool calls GoogleCalendarService(user,db).get_events(...)
        # Our mock_google_service fixture provides an instance of MockGoogleService from conftest.py
        # which replaces GoogleCalendarService.
        # So, mock_google_service *is* the instance of our MockGoogleService.
        # We make its get_events method raise an error that the actual GoogleCalendarService
        # would raise if the underlying GoogleCalendarClient.list_events had an HttpError.
        # The actual GoogleCalendarService.get_events wraps HttpError in a ValueError.

        # To be precise: list_events_tool -> GoogleCalendarService.get_events -> GoogleCalendarClient.list_events (raises HttpError)
        # GoogleCalendarService.get_events catches HttpError, logs, raises ValueError.
        # list_events_tool catches this ValueError, wraps in ToolExecutionError.
        # So, we need our *mocked service instance's get_events* to raise ValueError to simulate this.
        # (Or, we could make it raise HttpError, and verify the whole chain, but this is simpler for unit testing the wrapper)

        monkeypatch.setattr(
            mock_google_service, 
            "get_events", 
            Mock(side_effect=ValueError("Simulated error after catching HttpError from client"))
        )
        expected_internal_exception_type = ValueError
        expected_error_message_part = "simulated error after catching httperror from client"

    elif provider_name == "microsoft":
        # mock_microsoft_service is an instance of MockMicrosoftService from conftest.
        # We make its list_events method raise a ConnectionError.
        monkeypatch.setattr(
            mock_microsoft_service, 
            "list_events", 
            Mock(side_effect=ConnectionError("Simulated MS API communication failure"))
        )
        expected_internal_exception_type = ConnectionError
        expected_error_message_part = "simulated ms api communication failure"
        
    # Act & Assert
    with pytest.raises(ToolExecutionError) as exc_info:
        list_events_tool(
            user_id=str(test_user.id),
            provider=provider_name,
            db_session_factory=lambda: db_session,
            start_time=start_time_dt.isoformat(),
            end_time=end_time_dt.isoformat(),
            calendar_id="primary",
            max_results=10,
        )

    assert exc_info.value.original_exception is not None
    assert isinstance(exc_info.value.original_exception, expected_internal_exception_type)
    assert expected_error_message_part in str(exc_info.value.original_exception).lower()

def test_create_event_tool_google_success_with_conference(mock_google_service: MagicMock, test_user: User, db_session: Session):
    """Test create_event_tool happy path for Google provider with conference data."""
    start_dt = BASE_DATETIME + timedelta(hours=2)
    end_dt = BASE_DATETIME + timedelta(hours=3)

    input_data_dict = {
        "summary": "Google Meeting with Meet",
        "description": "A very important meeting with video call.",
        "location": "Virtual / Google Meet",
        "start_datetime": start_dt.isoformat(),
        "end_datetime": end_dt.isoformat(),
        "attendees": [{"email": "attendee1@example.com", "name": "Attendee One"}],
        "time_zone": "America/New_York",
        "conference_solution_key": "hangoutsMeet"  # Key for Google Meet
    }

    # Expected conference data that CalendarTools should pass to the service
    # The mock service (MockGoogleService.create_event) will receive an EventCreate model.
    # Its create_event method will then return a dict, which CalendarTools converts to JSON string,
    # and create_event_tool parses back to dict and then to EventSchema.

    # The mock_google_service fixture is an instance of MockGoogleService,
    # and its .create_event method was wrapped with MagicMock in conftest.py

    # Act
    # Provide db_session_factory for CalendarTools initialization within the wrapper
    result_output = create_event_tool(
        user_id=str(test_user.id),
        input_data=input_data_dict,
        db_session_factory=lambda: db_session
    )

    # Assert Output
    assert isinstance(result_output, CreateEventOutput)
    event_schema = result_output.event
    assert isinstance(event_schema, EventSchema)
    assert event_schema.summary == input_data_dict["summary"]
    assert event_schema.description == input_data_dict["description"]
    assert event_schema.location == input_data_dict["location"]
    assert event_schema.start_time.isoformat() == start_dt.replace(tzinfo=timezone.utc).isoformat() # Assuming UTC normalization
    assert event_schema.end_time.isoformat() == end_dt.replace(tzinfo=timezone.utc).isoformat()
    assert len(event_schema.attendees) == 1
    assert event_schema.attendees[0].email == "attendee1@example.com"
    assert event_schema.time_zone == "America/New_York" # Should be preserved

    # Assert conference_data in the output (comes from mock service's response)
    # MockGoogleService.create_event adds conferenceData to its response if present in EventCreate input.
    # The structure here should match what MockGoogleService puts in its response.
    expected_output_conference_data = {
        "createRequest": {
            "requestId": ANY, # This will be a UUID string
            "conferenceSolutionKey": {"type": "hangoutsMeet"}
        }
        # Potentially other fields if the mock adds them, e.g., entryPoints, notes
    }
    assert event_schema.conference_data is not None
    assert event_schema.conference_data["createRequest"]["conferenceSolutionKey"]["type"] == "hangoutsMeet"
    assert isinstance(event_schema.conference_data["createRequest"]["requestId"], str)

    # Assert call to mock service
    mock_google_service.create_event.assert_called_once()
    call_args = mock_google_service.create_event.call_args[0] # Get positional arguments
    # call_kwargs = mock_google_service.create_event.call_args[1] # Get keyword arguments
    
    assert len(call_args) > 0
    called_event_create_model = call_args[0] # First arg is event_create: EventCreate
    assert isinstance(called_event_create_model, EventCreate)
    
    assert called_event_create_model.summary == input_data_dict["summary"]
    assert called_event_create_model.time_slot.start == start_dt # CalendarTools converts ISO string to datetime
    assert called_event_create_model.time_slot.end == end_dt
    assert called_event_create_model.time_zone == input_data_dict["time_zone"]
    assert len(called_event_create_model.attendees) == 1
    assert called_event_create_model.attendees[0].email == "attendee1@example.com"

    # Assert conference_data passed to the service
    assert called_event_create_model.conference_data is not None
    assert called_event_create_model.conference_data["createRequest"]["conferenceSolutionKey"]["type"] == "hangoutsMeet"
    assert isinstance(called_event_create_model.conference_data["createRequest"]["requestId"], str)
    # Verify it's a UUID string if possible, or just check for presence and type
    UUID(called_event_create_model.conference_data["createRequest"]["requestId"]) # This will raise ValueError if not a valid UUID


@pytest.mark.parametrize("provider_name", ["google"]) # Temporarily limit to google
def test_create_event_tool_missing_required_fields(provider_name: str, test_user: User, db_session: Session):
    """Test create_event_tool with missing required fields (summary)."""
    # ... (rest of the code remains the same)

def test_create_event_tool_microsoft_auth_failure_on_api_call(
    mock_microsoft_service: MagicMock, 
    test_user: User, 
    db_session: Session
):
    """Test create_event_tool with auth failure during Microsoft API call."""
    start_dt = BASE_DATETIME + timedelta(hours=1)
    end_dt = BASE_DATETIME + timedelta(hours=2)

    input_data_dict = {
        "summary": "Trigger MS Auth Failure", # This summary triggers the mock error
        "start_datetime": start_dt.isoformat(),
        "end_datetime": end_dt.isoformat(),
        "time_zone": "UTC",
        "provider_name": "microsoft"
    }

    # Ensure user has a token that would otherwise allow init to pass
    test_user.microsoft_access_token = TokenEncryption.encrypt("dummy_ms_access_token_for_auth_fail_test")
    db_session.add(test_user)
    db_session.commit()

    with pytest.raises(ToolExecutionError) as excinfo:
        create_event_tool(
            user_id=str(test_user.id),
            input_data=input_data_dict,
            db_session_factory=lambda: db_session
        )
    
    assert excinfo.value.original_exception is not None
    assert isinstance(excinfo.value.original_exception, HTTPException)
    assert excinfo.value.original_exception.status_code == 401
    assert "Invalid or expired MS token during API call" in str(excinfo.value.original_exception.detail)
    # Service init should succeed, create_event should be called
    mock_microsoft_service.assert_called_once_with(user=test_user, db_session=db_session)
    mock_microsoft_service.return_value.create_event.assert_called_once()


def test_create_event_tool_microsoft_missing_token_on_init(
    mock_microsoft_service: MagicMock, # Class patch, so this is the mock class itself
    test_user: User, 
    db_session: Session
):
    """Test create_event_tool when Microsoft service init fails due to missing token."""
    start_dt = BASE_DATETIME + timedelta(hours=1)
    end_dt = BASE_DATETIME + timedelta(hours=2)

    test_user.microsoft_access_token = None
    test_user.microsoft_refresh_token = None
    db_session.add(test_user)
    db_session.commit()

    input_data_dict = {
        "summary": "MS Event, Init Fail (Missing Token)",
        "start_datetime": start_dt.isoformat(),
        "end_datetime": end_dt.isoformat(),
        "time_zone": "UTC",
        "provider_name": "microsoft"
    }

    with pytest.raises(ToolExecutionError) as excinfo:
        create_event_tool(
            user_id=str(test_user.id),
            input_data=input_data_dict,
            db_session_factory=lambda: db_session
        )
    
    assert excinfo.value.original_exception is not None
    assert isinstance(excinfo.value.original_exception, HTTPException)
    assert excinfo.value.original_exception.status_code == 400
    assert "MockMicrosoftService: No Microsoft access token found for user." in str(excinfo.value.original_exception.detail)
    
    # Service class __init__ was called, which raised the error
    mock_microsoft_service.assert_called_once_with(user=test_user, db_session=db_session)
    # The create_event method on the instance should not have been called
    mock_microsoft_service.return_value.create_event.assert_not_called()


def test_create_event_tool_microsoft_token_decryption_failure_on_init(
    mock_microsoft_service: MagicMock, # Class patch
    test_user: User, 
    db_session: Session
):
    """Test create_event_tool when Microsoft service init fails due to token decryption error."""
    start_dt = BASE_DATETIME + timedelta(hours=1)
    end_dt = BASE_DATETIME + timedelta(hours=2)

    # This specific raw token value triggers decryption error in MockMicrosoftService
    test_user.microsoft_access_token = "bad_encrypted_ms_token_for_mock"
    test_user.microsoft_refresh_token = TokenEncryption.encrypt("dummy_ms_refresh_token")
    db_session.add(test_user)
    db_session.commit()

    input_data_dict = {
        "summary": "MS Event, Init Fail (Decryption Error)",
        "start_datetime": start_dt.isoformat(),
        "end_datetime": end_dt.isoformat(),
        "time_zone": "UTC",
        "provider_name": "microsoft"
    }

    with pytest.raises(ToolExecutionError) as excinfo:
        create_event_tool(
            user_id=str(test_user.id),
            input_data=input_data_dict,
            db_session_factory=lambda: db_session
        )
    
    assert excinfo.value.original_exception is not None
    assert isinstance(excinfo.value.original_exception, ValueError)
    assert "MockMicrosoftService: Failed to decrypt MS token." in str(excinfo.value.original_exception)

    # Service class __init__ was called, which raised the error
    mock_microsoft_service.assert_called_once_with(user=test_user, db_session=db_session)
    # The create_event method on the instance should not have been called
    mock_microsoft_service.return_value.create_event.assert_not_called()


@pytest.mark.parametrize("provider_name", providers)
def test_reschedule_event_tool_google_success(
    provider_name: str,
    mock_google_service: MagicMock,
    mock_microsoft_service: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    if provider_name != "google":
        pytest.skip("Test is specific to Google provider success scenario.")
    # TODO: Implement actual test logic for rescheduling an event successfully with Google.
    # This might involve:
    # 1. Setting up mock_google_service.update_event to return a mock updated event.
    # 2. Preparing RescheduleEventInput data.
    # 3. Calling reschedule_event_tool.
    # 4. Asserting the output and that mock_google_service.update_event was called correctly.
    pass


@patch('app.agent.tools.GoogleCalendarService')
def test_reschedule_event_tool_google_service_init_failure(
    MockGoogleCalendarService: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test reschedule_event_tool when GoogleCalendarService fails to initialize."""
    MockGoogleCalendarService.side_effect = TokenDecryptionError("Failed to decrypt token")

    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name="google",
        event_id="any_event_id",
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1)
    )

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    
    assert "An unexpected error occurred" in str(excinfo.value) # The wrapper's generic error message
    assert isinstance(excinfo.value.original_exception, TokenDecryptionError)
    assert "Failed to decrypt token" in str(excinfo.value.original_exception)
    MockGoogleCalendarService.assert_called_once_with(user=test_user, db=ANY)


@patch('app.agent.tools.MicrosoftCalendarService')
def test_reschedule_event_tool_microsoft_service_init_failure(
    MockMicrosoftCalendarService: MagicMock,
    test_user: User,
    db_session_factory: Callable[[], Session]
):
    """Test reschedule_event_tool when MicrosoftCalendarService fails to initialize."""
    MockMicrosoftCalendarService.side_effect = ConnectionError("MS Graph API connection failed")

    now = datetime.now(timezone.utc)
    input_data = RescheduleEventInput(
        provider_name="microsoft",
        event_id="any_event_id",
        new_start_datetime=now + timedelta(days=1),
        new_end_datetime=now + timedelta(days=1, hours=1)
    )

    with pytest.raises(ToolExecutionError) as excinfo:
        reschedule_event_tool(
            user_id=str(test_user.id),
            input_data=input_data,
            db_session_factory=db_session_factory
        )
    
    assert "An unexpected error occurred" in str(excinfo.value) # The wrapper's generic error message
    assert isinstance(excinfo.value.original_exception, ConnectionError)
    assert "MS Graph API connection failed" in str(excinfo.value.original_exception)
    # The mock MicrosoftCalendarService in conftest takes 'credentials', not user/db directly in its __init__
    # CalendarTools.__init__ calls it with: self.calendar_service = MicrosoftCalendarService(credentials="mock_credentials")
    # So, we check if it was called. The arguments might differ if the actual MS service changes.
    MockMicrosoftCalendarService.assert_called_once()
