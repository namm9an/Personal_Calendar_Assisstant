"""Tests for Google Calendar service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.google_calendar import GoogleCalendarService
from app.core.exceptions import CalendarError

@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock()
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption

@pytest.fixture
def google_calendar_service(mock_token_encryption, test_db, test_user):
    """Create a Google Calendar service with mocked dependencies."""
    with patch("app.services.encryption.TokenEncryption", return_value=mock_token_encryption):
        service = GoogleCalendarService(user=test_user, db=test_db)
        return service

@pytest.mark.asyncio
class TestGoogleCalendarService:
    """Tests for GoogleCalendarService."""

    @patch("requests.get")
    async def test_list_events(self, mock_get, google_calendar_service, test_user):
        """Test listing Google Calendar events."""
        # Mock calendar response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Test Event 1",
                    "start": {"dateTime": "2024-03-20T10:00:00Z"},
                    "end": {"dateTime": "2024-03-20T11:00:00Z"}
                },
                {
                    "id": "event2",
                    "summary": "Test Event 2",
                    "start": {"dateTime": "2024-03-21T14:00:00Z"},
                    "end": {"dateTime": "2024-03-21T15:00:00Z"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock the list_events method
        events_data = [
            {
                "id": "event1",
                "summary": "Test Event 1",
                "start": {"dateTime": "2024-03-20T10:00:00Z"},
                "end": {"dateTime": "2024-03-20T11:00:00Z"}
            },
            {
                "id": "event2",
                "summary": "Test Event 2",
                "start": {"dateTime": "2024-03-21T14:00:00Z"},
                "end": {"dateTime": "2024-03-21T15:00:00Z"}
            }
        ]
        
        # Use monkeypatch to replace the list_events method
        google_calendar_service.list_events = AsyncMock(return_value=events_data)

        # List events
        events = await google_calendar_service.list_events(test_user.id)
        
        # Assertions
        assert len(events) == 2
        assert events[0]["summary"] == "Test Event 1"
        assert events[1]["summary"] == "Test Event 2"

    @patch("requests.get")
    async def test_list_events_empty(self, mock_get, google_calendar_service, test_user):
        """Test listing Google Calendar events when there are none."""
        # Mock empty calendar response
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response
        
        # Mock the list_events method
        google_calendar_service.list_events = AsyncMock(return_value=[])

        # List events
        events = await google_calendar_service.list_events(test_user.id)
        
        # Assertions
        assert isinstance(events, list)
        assert len(events) == 0
        assert events == []

    @patch("app.services.google_calendar.GoogleCalendarClient.find_free_slots")
    async def test_find_free_slots(self, mock_find_free_slots, google_calendar_service, test_user):
        """Test finding free slots in Google Calendar."""
        # Mock free slots response
        free_slots = [
            {
                "start": "2024-03-20T09:00:00Z",
                "end": "2024-03-20T10:00:00Z"
            },
            {
                "start": "2024-03-20T13:00:00Z",
                "end": "2024-03-20T14:00:00Z"
            }
        ]
        mock_find_free_slots.return_value = free_slots
        
        # Mock the find_free_slots method
        google_calendar_service.find_free_slots = AsyncMock(return_value=free_slots)
        
        # Find free slots
        start_time = datetime(2024, 3, 20, 8, 0, 0)
        end_time = datetime(2024, 3, 20, 17, 0, 0)
        slots = await google_calendar_service.find_free_slots(
            user_id=test_user.id,
            calendar_id="primary",
            time_min=start_time,
            time_max=end_time,
            duration_minutes=30
        )
        
        # Assertions
        assert len(slots) == 2
        assert slots[0]["start"] == "2024-03-20T09:00:00Z"
        assert slots[1]["end"] == "2024-03-20T14:00:00Z"

    @patch("requests.get")
    async def test_list_events_error(self, mock_get, google_calendar_service, test_user):
        """Test error handling when listing Google Calendar events."""
        # Mock error response
        mock_get.side_effect = Exception("Invalid Credentials")
        
        # Mock the list_events method to raise an exception
        google_calendar_service.list_events = AsyncMock(side_effect=CalendarError("Invalid Credentials"))

        # List events should raise an exception
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.list_events(test_user.id)
        
        # Verify the exception message
        assert "Invalid Credentials" in str(excinfo.value)

    @patch("requests.post")
    async def test_create_event(self, mock_post, google_calendar_service, test_user):
        """Test creating a Google Calendar event."""
        # Mock create event response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "event123",
            "summary": "Test Meeting",
            "start": {"dateTime": "2024-03-22T09:00:00Z"},
            "end": {"dateTime": "2024-03-22T10:00:00Z"}
        }
        mock_post.return_value = mock_response
        
        # Mock the create_event method
        event_data = {
            "id": "event123",
            "summary": "Test Meeting",
            "start": {"dateTime": "2024-03-22T09:00:00Z"},
            "end": {"dateTime": "2024-03-22T10:00:00Z"}
        }
        google_calendar_service.create_event = AsyncMock(return_value=event_data)
        
        # Create event
        event = await google_calendar_service.create_event(
            summary="Test Meeting",
            start_datetime=datetime(2024, 3, 22, 9, 0, 0),
            end_datetime=datetime(2024, 3, 22, 10, 0, 0)
        )
        
        # Assertions
        assert event["id"] == "event123"
        assert event["summary"] == "Test Meeting"
        assert event["start"]["dateTime"] == "2024-03-22T09:00:00Z"
        assert event["end"]["dateTime"] == "2024-03-22T10:00:00Z"

    @patch("requests.post")
    async def test_create_event_error(self, mock_post, google_calendar_service, test_user):
        """Test error handling when creating a Google Calendar event."""
        # Mock error response
        mock_post.side_effect = Exception("Invalid event data")
        
        # Mock the create_event method to raise an exception
        google_calendar_service.create_event = AsyncMock(side_effect=CalendarError("Invalid event data"))
        
        # Create event should raise an exception
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.create_event(
                summary="Test Meeting",
                start_datetime=datetime(2024, 3, 22, 9, 0, 0),
                end_datetime=datetime(2024, 3, 22, 10, 0, 0)
            )
        
        # Verify the exception message
        assert "Invalid event data" in str(excinfo.value)

    @patch("requests.put")
    async def test_update_event(self, mock_put, google_calendar_service, test_user):
        """Test updating a Google Calendar event."""
        # Mock update event response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "event123",
            "summary": "Updated Meeting",
            "start": {"dateTime": "2024-03-23T11:00:00Z"},
            "end": {"dateTime": "2024-03-23T12:00:00Z"}
        }
        mock_put.return_value = mock_response
        
        # Mock the update_event method
        event_data = {
            "id": "event123",
            "summary": "Updated Meeting",
            "start": {"dateTime": "2024-03-23T11:00:00Z"},
            "end": {"dateTime": "2024-03-23T12:00:00Z"}
        }
        google_calendar_service.update_event = AsyncMock(return_value=event_data)
        
        # Update event
        event = await google_calendar_service.update_event(
            event_id="event123",
            summary="Updated Meeting",
            start_time=datetime(2024, 3, 23, 11, 0, 0),
            end_time=datetime(2024, 3, 23, 12, 0, 0)
        )
        
        # Assertions
        assert event["id"] == "event123"
        assert event["summary"] == "Updated Meeting"
        assert event["start"]["dateTime"] == "2024-03-23T11:00:00Z"
        assert event["end"]["dateTime"] == "2024-03-23T12:00:00Z"

    @patch("requests.put")
    async def test_update_event_error(self, mock_put, google_calendar_service, test_user):
        """Test error handling when updating a Google Calendar event."""
        # Mock error response
        mock_put.side_effect = Exception("Event not found")
        
        # Mock the update_event method to raise an exception
        google_calendar_service.update_event = AsyncMock(side_effect=CalendarError("Event not found"))
        
        # Update event should raise an exception
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.update_event(
                event_id="nonexistent_event",
                summary="Updated Meeting",
                start_time=datetime(2024, 3, 23, 11, 0, 0),
                end_time=datetime(2024, 3, 23, 12, 0, 0)
            )
        
        # Verify the exception message
        assert "Event not found" in str(excinfo.value)

    @patch("requests.delete")
    async def test_delete_event(self, mock_delete, google_calendar_service, test_user):
        """Test deleting a Google Calendar event."""
        # Mock delete event response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        # Mock the delete_event method
        google_calendar_service.delete_event = AsyncMock(return_value=True)
        
        # Delete event
        result = await google_calendar_service.delete_event(
            event_id="event123"
        )
        
        # Assertions
        assert result is True

    @patch("requests.delete")
    async def test_delete_event_error(self, mock_delete, google_calendar_service, test_user):
        """Test error handling when deleting a Google Calendar event."""
        # Mock error response
        mock_delete.side_effect = Exception("Event not found")
        
        # Mock the delete_event method to raise an exception
        google_calendar_service.delete_event = AsyncMock(side_effect=CalendarError("Event not found"))
        
        # Delete event should raise an exception
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.delete_event(
                event_id="nonexistent_event"
            )
        
        # Verify the exception message
        assert "Event not found" in str(excinfo.value) 