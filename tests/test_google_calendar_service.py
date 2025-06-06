"""Tests for Google Calendar service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from app.services.google_calendar import GoogleCalendarService
from app.core.exceptions import CalendarError

@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock()
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption

@pytest.fixture
def google_calendar_service(mock_token_encryption, test_db):
    """Create a Google Calendar service with mocked dependencies."""
    with patch("app.services.google_calendar.TokenEncryption", return_value=mock_token_encryption):
        service = GoogleCalendarService(test_db)
        return service

class TestGoogleCalendarService:
    """Tests for GoogleCalendarService."""

    @patch("app.services.google_calendar.requests.get")
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

        # List events
        events = await google_calendar_service.list_events(test_user)

        # Verify events
        assert len(events) == 2
        assert events[0]["id"] == "event1"
        assert events[0]["summary"] == "Test Event 1"
        assert events[1]["id"] == "event2"
        assert events[1]["summary"] == "Test Event 2"

    @patch("app.services.google_calendar.requests.get")
    async def test_list_events_error(self, mock_get, google_calendar_service, test_user):
        """Test error handling when listing Google Calendar events."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": 401,
                "message": "Invalid Credentials"
            }
        }
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        # Attempt to list events
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.list_events(test_user)
        
        assert "Invalid Credentials" in str(excinfo.value)

    @patch("app.services.google_calendar.requests.post")
    async def test_create_event(self, mock_post, google_calendar_service, test_user):
        """Test creating a Google Calendar event."""
        # Mock event creation response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "new_event",
            "summary": "New Test Event",
            "start": {"dateTime": "2024-03-22T09:00:00Z"},
            "end": {"dateTime": "2024-03-22T10:00:00Z"}
        }
        mock_post.return_value = mock_response

        # Create event
        event_data = {
            "summary": "New Test Event",
            "start": {"dateTime": "2024-03-22T09:00:00Z"},
            "end": {"dateTime": "2024-03-22T10:00:00Z"}
        }
        event = await google_calendar_service.create_event(test_user, event_data)

        # Verify event creation
        assert event["id"] == "new_event"
        assert event["summary"] == "New Test Event"
        assert event["start"]["dateTime"] == "2024-03-22T09:00:00Z"
        assert event["end"]["dateTime"] == "2024-03-22T10:00:00Z"

    @patch("app.services.google_calendar.requests.post")
    async def test_create_event_error(self, mock_post, google_calendar_service, test_user):
        """Test error handling when creating a Google Calendar event."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": 400,
                "message": "Invalid event data"
            }
        }
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Attempt to create event
        event_data = {
            "summary": "Invalid Event",
            "start": {"dateTime": "invalid-date"},
            "end": {"dateTime": "invalid-date"}
        }
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.create_event(test_user, event_data)
        
        assert "Invalid event data" in str(excinfo.value)

    @patch("app.services.google_calendar.requests.put")
    async def test_update_event(self, mock_put, google_calendar_service, test_user):
        """Test updating a Google Calendar event."""
        # Mock event update response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "event1",
            "summary": "Updated Test Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z"},
            "end": {"dateTime": "2024-03-23T12:00:00Z"}
        }
        mock_put.return_value = mock_response

        # Update event
        event_id = "event1"
        event_data = {
            "summary": "Updated Test Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z"},
            "end": {"dateTime": "2024-03-23T12:00:00Z"}
        }
        event = await google_calendar_service.update_event(test_user, event_id, event_data)

        # Verify event update
        assert event["id"] == "event1"
        assert event["summary"] == "Updated Test Event"
        assert event["start"]["dateTime"] == "2024-03-23T11:00:00Z"
        assert event["end"]["dateTime"] == "2024-03-23T12:00:00Z"

    @patch("app.services.google_calendar.requests.put")
    async def test_update_event_error(self, mock_put, google_calendar_service, test_user):
        """Test error handling when updating a Google Calendar event."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": 404,
                "message": "Event not found"
            }
        }
        mock_response.status_code = 404
        mock_put.return_value = mock_response

        # Attempt to update event
        event_id = "nonexistent_event"
        event_data = {
            "summary": "Updated Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z"},
            "end": {"dateTime": "2024-03-23T12:00:00Z"}
        }
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.update_event(test_user, event_id, event_data)
        
        assert "Event not found" in str(excinfo.value)

    @patch("app.services.google_calendar.requests.delete")
    async def test_delete_event(self, mock_delete, google_calendar_service, test_user):
        """Test deleting a Google Calendar event."""
        # Mock successful deletion
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Delete event
        event_id = "event1"
        await google_calendar_service.delete_event(test_user, event_id)

        # Verify deletion request
        mock_delete.assert_called_once()

    @patch("app.services.google_calendar.requests.delete")
    async def test_delete_event_error(self, mock_delete, google_calendar_service, test_user):
        """Test error handling when deleting a Google Calendar event."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": 404,
                "message": "Event not found"
            }
        }
        mock_response.status_code = 404
        mock_delete.return_value = mock_response

        # Attempt to delete event
        event_id = "nonexistent_event"
        with pytest.raises(CalendarError) as excinfo:
            await google_calendar_service.delete_event(test_user, event_id)
        
        assert "Event not found" in str(excinfo.value) 