"""Simple tests for calendar tools without complex dependencies."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId

from src.core.exceptions import ToolExecutionError
from src.calendar_tool_wrappers import (
    list_events_tool,
    find_free_slots_tool,
    create_event_tool
)
from src.tool_schemas import (
    ListEventsInput,
    ListEventsOutput,
    FreeSlotsInput,
    FreeSlotsOutput,
    EventSchema,
    AttendeeSchema,
    CreateEventInput,
    CreateEventOutput
)

# Mock user data
MOCK_USER = {
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "id": "507f1f77bcf86cd799439011",
    "email": "test@example.com",
    "name": "Test User",
    "google_access_token": "test_google_token",
    "microsoft_access_token": "test_microsoft_token",
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

# Mock calendar service
class MockCalendarService:
    async def list_events(self, *args, **kwargs):
        return [
            {
                "id": "mock_event_1",
                "summary": "Mock Event",
                "start": {"dateTime": datetime.utcnow().isoformat()},
                "end": {"dateTime": (datetime.utcnow() + timedelta(hours=1)).isoformat()},
                "attendees": [{"email": "test@example.com"}],
                "htmlLink": "https://calendar.google.com/event?id=123"
            }
        ]
    
    async def find_free_slots(self, *args, **kwargs):
        return [
            {
                "start": datetime.utcnow().isoformat(),
                "end": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
            }
        ]
    
    async def create_event(self, *args, **kwargs):
        return {
            "id": "new_event_id",
            "summary": "New Event",
            "start": {"dateTime": datetime.utcnow().isoformat()},
            "end": {"dateTime": (datetime.utcnow() + timedelta(hours=1)).isoformat()},
            "htmlLink": "https://calendar.google.com/event?id=new123"
        }

@pytest.mark.asyncio
async def test_list_events_tool_success():
    """Test list_events_tool with mocked dependencies."""
    user_id = str(ObjectId())
    
    # Create a mock coroutine for get_user_by_id that returns our mock user
    async def mock_get_user_by_id_coroutine(*args, **kwargs):
        return MOCK_USER
    
    # Create a mock coroutine for the calendar service
    async def mock_get_calendar_service(*args, **kwargs):
        return MockCalendarService()
    
    # Mock the OAuthService.get_user_by_id method
    with patch("src.calendar_tool_wrappers.OAuthService") as MockOAuthService:
        # Setup the mock
        mock_oauth_instance = MockOAuthService.return_value
        mock_oauth_instance.get_user_by_id = mock_get_user_by_id_coroutine
        
        # Mock the calendar service
        with patch("src.calendar_tool_wrappers.get_calendar_service", side_effect=mock_get_calendar_service):
            # Call the function
            result = await list_events_tool(ListEventsInput(
                provider="google",
                user_id=user_id,
                start=datetime.utcnow().isoformat(),
                end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
            ))
            
            # Debug prints
            print(f"Result type: {type(result)}")
            print(f"Expected type: {ListEventsOutput}")
            print(f"Result: {result}")
            
            # Verify the result by checking attributes instead of type
            assert hasattr(result, 'events')
            assert len(result.events) == 1
            assert result.events[0].id == "mock_event_1"
            assert result.events[0].summary == "Mock Event"

@pytest.mark.asyncio
async def test_list_events_tool_user_not_found():
    """Test list_events_tool when user is not found."""
    user_id = str(ObjectId())
    
    # Create a mock coroutine for get_user_by_id that returns None
    async def mock_get_user_by_id_coroutine(*args, **kwargs):
        return None
    
    # Mock the OAuthService.get_user_by_id method to return None
    with patch("src.calendar_tool_wrappers.OAuthService") as MockOAuthService:
        # Setup the mock
        mock_oauth_instance = MockOAuthService.return_value
        mock_oauth_instance.get_user_by_id = mock_get_user_by_id_coroutine
        
        # Call the function and expect an exception
        with pytest.raises(ToolExecutionError) as excinfo:
            await list_events_tool(ListEventsInput(
                provider="google",
                user_id=user_id,
                start=datetime.utcnow().isoformat(),
                end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
            ))
        
        # Verify the exception message
        assert "User not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_find_free_slots_tool_success():
    """Test find_free_slots_tool with mocked dependencies."""
    user_id = str(ObjectId())
    
    # Create a mock coroutine for get_user_by_id that returns our mock user
    async def mock_get_user_by_id_coroutine(*args, **kwargs):
        return MOCK_USER
    
    # Create a mock coroutine for the calendar service
    async def mock_get_calendar_service(*args, **kwargs):
        return MockCalendarService()
    
    # Mock the OAuthService.get_user_by_id method
    with patch("src.calendar_tool_wrappers.OAuthService") as MockOAuthService:
        # Setup the mock
        mock_oauth_instance = MockOAuthService.return_value
        mock_oauth_instance.get_user_by_id = mock_get_user_by_id_coroutine
        
        # Mock the calendar service
        with patch("src.calendar_tool_wrappers.get_calendar_service", side_effect=mock_get_calendar_service):
            # Call the function
            result = await find_free_slots_tool(FreeSlotsInput(
                provider="google",
                user_id=user_id,
                duration_minutes=30,
                range_start=datetime.utcnow(),
                range_end=datetime.utcnow() + timedelta(hours=2)
            ))
            
            # Verify the result by checking attributes instead of type
            assert hasattr(result, 'slots')
            assert len(result.slots) == 1

@pytest.mark.asyncio
async def test_create_event_tool_success():
    """Test create_event_tool with mocked dependencies."""
    user_id = str(ObjectId())
    
    # Create a mock coroutine for get_user_by_id that returns our mock user
    async def mock_get_user_by_id_coroutine(*args, **kwargs):
        return MOCK_USER
    
    # Create a mock coroutine for the calendar service
    async def mock_get_calendar_service(*args, **kwargs):
        return MockCalendarService()
    
    # Mock the OAuthService.get_user_by_id method
    with patch("src.calendar_tool_wrappers.OAuthService") as MockOAuthService:
        # Setup the mock
        mock_oauth_instance = MockOAuthService.return_value
        mock_oauth_instance.get_user_by_id = mock_get_user_by_id_coroutine
        
        # Mock the calendar service
        with patch("src.calendar_tool_wrappers.get_calendar_service", side_effect=mock_get_calendar_service):
            # Call the function
            result = await create_event_tool(CreateEventInput(
                provider="google",
                user_id=user_id,
                summary="New Event",
                start=datetime.utcnow().isoformat(),
                end=(datetime.utcnow() + timedelta(hours=1)).isoformat()
            ))
            
            # Verify the result by checking attributes instead of type
            assert hasattr(result, 'event')
            assert result.event.id == "new_event_id"
            assert result.event.summary == "New Event" 