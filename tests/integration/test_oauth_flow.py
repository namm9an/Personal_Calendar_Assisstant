import pytest
from datetime import datetime, timedelta
from src.services.oauth_service import OAuthService
from src.calendar_tool_wrappers import (
    list_events_tool,
    find_free_slots_tool,
    create_event_tool,
    reschedule_event_tool,
    cancel_event_tool
)
from src.tool_schemas import (
    ListEventsInput,
    FreeSlotsInput,
    CreateEventInput,
    RescheduleEventInput,
    CancelEventInput,
    AttendeeSchema
)
from src.db.test_config import Base, engine, TestingSessionLocal

# Create tables
Base.metadata.create_all(bind=engine)

@pytest.fixture
def oauth_service():
    return OAuthService()

@pytest.fixture
def test_user(oauth_service):
    # Create a test user with mock tokens
    user = oauth_service.create_or_update_user_tokens(
        email="test@example.com",
        provider="google",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token"
    )
    return user

def test_oauth_token_storage(test_user, oauth_service):
    # Verify tokens are stored and can be retrieved
    access_token, refresh_token = oauth_service.get_user_tokens(test_user.id, "google")
    assert access_token == "mock_access_token"
    assert refresh_token == "mock_refresh_token"

def test_list_events_with_tokens(test_user):
    now = datetime.utcnow()
    input_data = ListEventsInput(
        provider="google",
        user_id=str(test_user.id),
        start=now,
        end=now + timedelta(hours=1)
    )
    output = list_events_tool(input_data)
    assert isinstance(output.events, list)

def test_create_event_with_tokens(test_user):
    now = datetime.utcnow()
    input_data = CreateEventInput(
        provider="google",
        user_id=str(test_user.id),
        summary="Test Meeting",
        start=now + timedelta(hours=1),
        end=now + timedelta(hours=2),
        description="Test Description",
        location="Test Location",
        attendees=[AttendeeSchema(email="attendee@example.com")]
    )
    output = create_event_tool(input_data)
    assert output.event.summary == "Test Meeting"

def test_find_free_slots_with_tokens(test_user):
    now = datetime.utcnow()
    input_data = FreeSlotsInput(
        provider="google",
        user_id=str(test_user.id),
        duration_minutes=30,
        range_start=now,
        range_end=now + timedelta(days=1)
    )
    output = find_free_slots_tool(input_data)
    assert len(output.slots) > 0

def test_reschedule_event_with_tokens(test_user):
    now = datetime.utcnow()
    input_data = RescheduleEventInput(
        provider="google",
        user_id=str(test_user.id),
        event_id="test_event_id",
        new_start=now + timedelta(days=1)
    )
    output = reschedule_event_tool(input_data)
    assert output.event.start == input_data.new_start

def test_cancel_event_with_tokens(test_user):
    input_data = CancelEventInput(
        provider="google",
        user_id=str(test_user.id),
        event_id="test_event_id"
    )
    output = cancel_event_tool(input_data)
    assert output.success is True

def test_missing_tokens(test_user, oauth_service):
    # Clear tokens
    oauth_service.create_or_update_user_tokens(
        email=test_user.email,
        provider="google",
        access_token=None,
        refresh_token=None
    )
    
    now = datetime.utcnow()
    input_data = ListEventsInput(
        provider="google",
        user_id=str(test_user.id),
        start=now,
        end=now + timedelta(hours=1)
    )
    
    with pytest.raises(Exception) as exc_info:
        list_events_tool(input_data)
    assert "No credentials found" in str(exc_info.value) 