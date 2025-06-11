import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.calendar_agent import run_calendar_agent
from src.core.exceptions import ToolExecutionError
from app.models.mongodb_models import User
from src.calendar_tool_wrappers import (
    ListEventsOutput,
    FreeSlotsOutput,
    CreateEventOutput,
    UpdateEventOutput,
    DeleteEventOutput,
    RescheduleEventOutput,
    CancelEventOutput
)
from src.tool_schemas import EventSchema, FreeSlotSchema, AttendeeSchema

class MockUser:
    """Mock User object for testing"""
    def __init__(self):
        self.id = "test_user"
        self.name = "Test User"
        self.email = "test@example.com"
        self.google_access_token = "test_google_token" 
        self.microsoft_access_token = "test_microsoft_token"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class MockCalendarService:
    """Mock calendar service for testing"""
    async def list_events(self, **kwargs):
        return [{"id": "test1", "summary": "Test Event"}]
        
    async def find_free_slots(self, **kwargs):
        return [{"start": datetime.now().isoformat(), "end": (datetime.now() + timedelta(hours=1)).isoformat()}]
        
    async def create_event(self, event_data, calendar_id="primary"):
        return {
            "id": "new_event",
            "summary": event_data.get("summary", "Test Event"),
            "start": {"dateTime": datetime.now().isoformat()},
            "end": {"dateTime": (datetime.now() + timedelta(hours=1)).isoformat()}
        }
        
    async def update_event(self, event_id, event_data, calendar_id="primary"):
        return {
            "id": event_id,
            "summary": event_data.get("summary", "Updated Event"),
            "start": {"dateTime": datetime.now().isoformat()},
            "end": {"dateTime": (datetime.now() + timedelta(hours=1)).isoformat()}
        }
        
    async def get_event(self, event_id, calendar_id="primary"):
        return {
            "id": event_id,
            "summary": "Test Event",
            "start": {"dateTime": datetime.now().isoformat()},
            "end": {"dateTime": (datetime.now() + timedelta(hours=1)).isoformat()}
        }
        
    async def delete_event(self, event_id, calendar_id="primary"):
        return True
        
    async def cancel_event(self, event_id, start=None, end=None, calendar_id="primary"):
        return True

def create_mock_event_schema():
    """Helper function to create a mock EventSchema"""
    now = datetime.now()
    return EventSchema(
        id="mock_event_1",
        summary="Test Event",
        start=now.isoformat(),
        end=(now + timedelta(hours=1)).isoformat(),
        description="Test description",
        location="Test location",
        attendees=[],
        html_link="http://example.com/event"
    )

@pytest.fixture
def mock_oauth_service():
    """Create a mocked OAuthService for testing"""
    mock_service = MagicMock()
    mock_service.get_user_by_id = AsyncMock(return_value=MockUser())
    return mock_service

@pytest.mark.asyncio
@patch("src.calendar_tool_wrappers.OAuthService")
@patch("src.calendar_tool_wrappers.GoogleCalendarService")
@patch("src.calendar_tool_wrappers.MicrosoftCalendarService")
@patch("src.calendar_tool_wrappers.list_events_tool")
async def test_list_events(mock_list_events, mock_ms_service_class, mock_google_service_class, mock_oauth_class):
    """Test listing events."""
    # Set up the mocks
    mock_ms_service_class.return_value = MockCalendarService()
    mock_google_service_class.return_value = MockCalendarService()
    
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_user_by_id = AsyncMock(return_value=MockUser())
    mock_oauth_class.return_value = mock_oauth_instance
    
    # Mock the list_events_tool function
    mock_events = [create_mock_event_schema()]
    mock_list_events.return_value = ListEventsOutput(events=mock_events)
    
    result = await run_calendar_agent(
        text="list my events",
        user_id="test_user",
        provider="google"
    )
    assert "events" in result
    assert isinstance(result["events"], ListEventsOutput)

@pytest.mark.asyncio
@patch("src.calendar_tool_wrappers.OAuthService")
@patch("src.calendar_tool_wrappers.GoogleCalendarService")
@patch("src.calendar_tool_wrappers.MicrosoftCalendarService")
@patch("src.calendar_tool_wrappers.find_free_slots_tool")
async def test_find_free_slots(mock_find_slots, mock_ms_service_class, mock_google_service_class, mock_oauth_class):
    """Test finding free slots."""
    # Set up the mocks
    mock_ms_service_class.return_value = MockCalendarService()
    mock_google_service_class.return_value = MockCalendarService()
    
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_user_by_id = AsyncMock(return_value=MockUser())
    mock_oauth_class.return_value = mock_oauth_instance
    
    # Mock the find_free_slots_tool function
    now = datetime.now()
    mock_slots = [
        FreeSlotSchema(
            start=now.isoformat(),
            end=(now + timedelta(hours=1)).isoformat()
        )
    ]
    mock_find_slots.return_value = FreeSlotsOutput(slots=mock_slots)
    
    result = await run_calendar_agent(
        text="find free slots for tomorrow",
        user_id="test_user",
        provider="google"
    )
    assert "slots" in result
    assert isinstance(result["slots"], FreeSlotsOutput)

@pytest.mark.asyncio
@patch("src.calendar_tool_wrappers.OAuthService")
@patch("src.calendar_tool_wrappers.GoogleCalendarService")
@patch("src.calendar_tool_wrappers.MicrosoftCalendarService")
@patch("src.calendar_tool_wrappers.create_event_tool")
async def test_create_event(mock_create_event, mock_ms_service_class, mock_google_service_class, mock_oauth_class):
    """Test creating an event."""
    # Set up the mocks
    mock_ms_service_class.return_value = MockCalendarService()
    mock_google_service_class.return_value = MockCalendarService()
    
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_user_by_id = AsyncMock(return_value=MockUser())
    mock_oauth_class.return_value = mock_oauth_instance
    
    # Mock create_event_tool
    event = create_mock_event_schema()
    mock_create_event.return_value = CreateEventOutput(event=event)
    
    result = await run_calendar_agent(
        text="create a meeting tomorrow at 2pm",
        user_id="test_user",
        provider="google"
    )
    assert "event" in result
    assert isinstance(result["event"], CreateEventOutput)

@pytest.mark.asyncio
@patch("src.calendar_tool_wrappers.OAuthService")
@patch("src.calendar_tool_wrappers.GoogleCalendarService")
@patch("src.calendar_tool_wrappers.MicrosoftCalendarService")
@patch("src.calendar_tool_wrappers.update_event_tool")
async def test_update_event(mock_update_event, mock_ms_service_class, mock_google_service_class, mock_oauth_class):
    """Test updating an event."""
    # Set up the mocks
    mock_ms_service_class.return_value = MockCalendarService()
    mock_google_service_class.return_value = MockCalendarService()
    
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_user_by_id = AsyncMock(return_value=MockUser())
    mock_oauth_class.return_value = mock_oauth_instance
    
    # Mock update_event_tool
    event = create_mock_event_schema()
    mock_update_event.return_value = UpdateEventOutput(event=event)
    
    result = await run_calendar_agent(
        text="update my meeting tomorrow to 3pm",
        user_id="test_user",
        provider="google"
    )
    assert "event" in result
    assert isinstance(result["event"], UpdateEventOutput)

@pytest.mark.asyncio
@patch("src.calendar_tool_wrappers.OAuthService")
@patch("src.calendar_tool_wrappers.GoogleCalendarService")
@patch("src.calendar_tool_wrappers.MicrosoftCalendarService")
@patch("src.calendar_tool_wrappers.delete_event_tool")
async def test_delete_event(mock_delete_event, mock_ms_service_class, mock_google_service_class, mock_oauth_class):
    """Test deleting an event."""
    # Set up the mocks
    mock_ms_service_class.return_value = MockCalendarService()
    mock_google_service_class.return_value = MockCalendarService()
    
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_user_by_id = AsyncMock(return_value=MockUser())
    mock_oauth_class.return_value = mock_oauth_instance
    
    # Mock delete_event_tool
    mock_delete_event.return_value = DeleteEventOutput(success=True)
    
    result = await run_calendar_agent(
        text="delete my meeting tomorrow",
        user_id="test_user",
        provider="google"
    )
    assert "success" in result
    assert isinstance(result["success"], DeleteEventOutput)

@pytest.mark.asyncio
@patch("src.services.calendar_agent.CalendarAgent._parse_action")
@patch("src.services.calendar_agent.reschedule_event_tool")
async def test_reschedule_event(mock_reschedule_event, mock_parse_action):
    """Test rescheduling an event."""
    # Force the _parse_action to return "reschedule_event"
    mock_parse_action.return_value = "reschedule_event"
    
    # Mock reschedule_event_tool
    event = create_mock_event_schema()
    mock_reschedule_event.return_value = RescheduleEventOutput(event=event)
    
    result = await run_calendar_agent(
        text="reschedule my meeting to next week",
        user_id="test_user",
        provider="google"
    )
    assert "event" in result
    assert isinstance(result["event"], RescheduleEventOutput)

@pytest.mark.asyncio
@patch("src.calendar_tool_wrappers.OAuthService")
@patch("src.calendar_tool_wrappers.GoogleCalendarService")
@patch("src.calendar_tool_wrappers.MicrosoftCalendarService")
@patch("src.calendar_tool_wrappers.cancel_event_tool")
async def test_cancel_event(mock_cancel_event, mock_ms_service_class, mock_google_service_class, mock_oauth_class):
    """Test canceling an event."""
    # Set up the mocks
    mock_ms_service_class.return_value = MockCalendarService()
    mock_google_service_class.return_value = MockCalendarService()
    
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_user_by_id = AsyncMock(return_value=MockUser())
    mock_oauth_class.return_value = mock_oauth_instance
    
    # Mock cancel_event_tool
    mock_cancel_event.return_value = CancelEventOutput(success=True)
    
    result = await run_calendar_agent(
        text="cancel my meeting tomorrow",
        user_id="test_user",
        provider="google"
    )
    assert "success" in result
    assert isinstance(result["success"], CancelEventOutput)

@pytest.mark.asyncio
async def test_invalid_provider():
    """Test with invalid provider."""
    with pytest.raises(ToolExecutionError):
        await run_calendar_agent(
            text="list my events",
            user_id="test_user",
            provider="invalid"
        )

@pytest.mark.asyncio
async def test_invalid_action():
    """Test with invalid action."""
    with pytest.raises(ToolExecutionError):
        await run_calendar_agent(
            text="invalid action",
            user_id="test_user",
            provider="google"
        ) 