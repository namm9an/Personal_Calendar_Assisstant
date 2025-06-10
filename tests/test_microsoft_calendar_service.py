"""Tests for Microsoft Calendar service."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ms_calendar import MicrosoftCalendarService
from app.core.exceptions import CalendarError, OAuthError

@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock()
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption

@pytest.fixture
def microsoft_calendar_service(mock_token_encryption, test_db, test_user):
    """Create a Microsoft Calendar service with mocked dependencies."""
    with patch("app.services.encryption.TokenEncryption", return_value=mock_token_encryption):
        service = MicrosoftCalendarService(user=test_user, db=test_db)
        return service

@pytest.mark.asyncio
class TestMicrosoftCalendarService:
    """Tests for MicrosoftCalendarService."""

    @patch("requests.get")
    async def test_list_events(self, mock_get, microsoft_calendar_service, test_user):
        """Test listing Microsoft Calendar events."""
        # Mock calendar response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "event1",
                    "subject": "Test Event 1",
                    "start": {"dateTime": "2024-03-20T10:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-03-20T11:00:00Z", "timeZone": "UTC"}
                },
                {
                    "id": "event2",
                    "subject": "Test Event 2",
                    "start": {"dateTime": "2024-03-21T14:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-03-21T15:00:00Z", "timeZone": "UTC"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock the list_events method
        events_data = [
            {
                "id": "event1",
                "subject": "Test Event 1",
                "start": {"dateTime": "2024-03-20T10:00:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2024-03-20T11:00:00Z", "timeZone": "UTC"}
            },
            {
                "id": "event2",
                "subject": "Test Event 2",
                "start": {"dateTime": "2024-03-21T14:00:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2024-03-21T15:00:00Z", "timeZone": "UTC"}
            }
        ]
        microsoft_calendar_service.list_events = AsyncMock(return_value=events_data)

        # List events
        events = await microsoft_calendar_service.list_events()
        
        # Assertions
        assert len(events) == 2
        assert events[0]["id"] == "event1"
        assert events[0]["subject"] == "Test Event 1"
        assert events[1]["id"] == "event2"
        assert events[1]["subject"] == "Test Event 2"

    @patch("requests.get")
    async def test_list_events_error(self, mock_get, microsoft_calendar_service, test_user):
        """Test error handling when listing Microsoft Calendar events."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidAuthenticationToken",
                "message": "Access token has expired"
            }
        }
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        # Mock the list_events method to raise an exception
        microsoft_calendar_service.list_events = AsyncMock(side_effect=CalendarError("Access token has expired"))

        # Attempt to list events
        with pytest.raises(CalendarError) as excinfo:
            await microsoft_calendar_service.list_events()
        
        # Verify the exception message
        assert "Access token has expired" in str(excinfo.value)

    @patch("requests.post")
    async def test_create_event(self, mock_post, microsoft_calendar_service, test_user):
        """Test creating a Microsoft Calendar event."""
        # Mock event creation response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "new_event",
            "subject": "New Test Event",
            "start": {"dateTime": "2024-03-22T09:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-22T10:00:00Z", "timeZone": "UTC"}
        }
        mock_post.return_value = mock_response
        
        # Mock the create_event method
        event_data = {
            "id": "new_event",
            "subject": "New Test Event",
            "start": {"dateTime": "2024-03-22T09:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-22T10:00:00Z", "timeZone": "UTC"}
        }
        microsoft_calendar_service.create_event = AsyncMock(return_value=event_data)
        
        # Create event
        event = await microsoft_calendar_service.create_event(
            event_data={
                "subject": "New Test Event",
                "start": {"dateTime": "2024-03-22T09:00:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2024-03-22T10:00:00Z", "timeZone": "UTC"}
            }
        )
        
        # Assertions
        assert event["id"] == "new_event"
        assert event["subject"] == "New Test Event"
        assert event["start"]["dateTime"] == "2024-03-22T09:00:00Z"
        assert event["end"]["dateTime"] == "2024-03-22T10:00:00Z"

    @patch("requests.post")
    async def test_create_event_error(self, mock_post, microsoft_calendar_service, test_user):
        """Test error handling when creating a Microsoft Calendar event."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "ErrorInvalidRequest",
                "message": "Invalid event data"
            }
        }
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        # Mock the create_event method to raise an exception
        microsoft_calendar_service.create_event = AsyncMock(side_effect=CalendarError("Invalid event data"))

        # Attempt to create event
        event_data = {
            "subject": "Invalid Event",
            "start": {"dateTime": "invalid-date", "timeZone": "UTC"},
            "end": {"dateTime": "invalid-date", "timeZone": "UTC"}
        }
        with pytest.raises(CalendarError) as excinfo:
            await microsoft_calendar_service.create_event(event_data=event_data)
        
        # Verify the exception message
        assert "Invalid event data" in str(excinfo.value)

    @patch("requests.patch")
    async def test_update_event(self, mock_patch, microsoft_calendar_service, test_user):
        """Test updating a Microsoft Calendar event."""
        # Mock update response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "event1",
            "subject": "Updated Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-23T12:00:00Z", "timeZone": "UTC"}
        }
        mock_patch.return_value = mock_response
        
        # Mock the update_event method
        updated_event = {
            "id": "event1",
            "subject": "Updated Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-23T12:00:00Z", "timeZone": "UTC"}
        }
        microsoft_calendar_service.update_event = AsyncMock(return_value=updated_event)

        # Update event
        event_id = "event1"
        event_data = {
            "subject": "Updated Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-23T12:00:00Z", "timeZone": "UTC"}
        }
        event = await microsoft_calendar_service.update_event(event_id=event_id, event_data=event_data)
        
        # Assertions
        assert event["id"] == "event1"
        assert event["subject"] == "Updated Event"
        assert event["start"]["dateTime"] == "2024-03-23T11:00:00Z"
        assert event["end"]["dateTime"] == "2024-03-23T12:00:00Z"

    @patch("requests.patch")
    async def test_update_event_error(self, mock_patch, microsoft_calendar_service, test_user):
        """Test error handling when updating a Microsoft Calendar event."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "ErrorItemNotFound",
                "message": "Event not found"
            }
        }
        mock_response.status_code = 404
        mock_patch.return_value = mock_response
        
        # Mock the update_event method to raise an exception
        microsoft_calendar_service.update_event = AsyncMock(side_effect=CalendarError("Event not found"))

        # Attempt to update event
        event_id = "nonexistent_event"
        event_data = {
            "subject": "Updated Event",
            "start": {"dateTime": "2024-03-23T11:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": "2024-03-23T12:00:00Z", "timeZone": "UTC"}
        }
        with pytest.raises(CalendarError) as excinfo:
            await microsoft_calendar_service.update_event(event_id=event_id, event_data=event_data)
        
        # Verify the exception message
        assert "Event not found" in str(excinfo.value)

    @patch("requests.delete")
    async def test_delete_event(self, mock_delete, microsoft_calendar_service, test_user):
        """Test deleting a Microsoft Calendar event."""
        # Mock successful deletion
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        # Mock the delete_event method
        microsoft_calendar_service.delete_event = AsyncMock(return_value=True)

        # Delete event
        event_id = "event1"
        result = await microsoft_calendar_service.delete_event(event_id=event_id)
        
        # Assertions
        assert result is True

    @patch("requests.delete")
    async def test_delete_event_error(self, mock_delete, microsoft_calendar_service, test_user):
        """Test error handling when deleting a Microsoft Calendar event."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "ErrorItemNotFound",
                "message": "Event not found"
            }
        }
        mock_response.status_code = 404
        mock_delete.return_value = mock_response
        
        # Mock the delete_event method to raise an exception
        microsoft_calendar_service.delete_event = AsyncMock(side_effect=CalendarError("Event not found"))

        # Attempt to delete event
        event_id = "nonexistent_event"
        with pytest.raises(CalendarError) as excinfo:
            await microsoft_calendar_service.delete_event(event_id=event_id)
        
        # Verify the exception message
        assert "Event not found" in str(excinfo.value)

    @patch("requests.get")
    async def test_list_calendars(self, mock_get, microsoft_calendar_service, test_user):
        """Test listing Microsoft calendars."""
        # Mock calendars response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "calendar1",
                    "name": "Calendar 1",
                    "canEdit": True
                },
                {
                    "id": "calendar2",
                    "name": "Calendar 2",
                    "canEdit": False
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock the list_calendars method
        calendars_data = [
            {
                "id": "calendar1",
                "name": "Calendar 1",
                "canEdit": True
            },
            {
                "id": "calendar2",
                "name": "Calendar 2",
                "canEdit": False
            }
        ]
        microsoft_calendar_service.list_calendars = AsyncMock(return_value=calendars_data)

        # List calendars
        calendars = await microsoft_calendar_service.list_calendars()
        
        # Assertions
        assert len(calendars) == 2
        assert calendars[0]["id"] == "calendar1"
        assert calendars[0]["name"] == "Calendar 1"
        assert calendars[1]["id"] == "calendar2"
        assert calendars[1]["name"] == "Calendar 2"

    @patch("requests.get")
    async def test_list_calendars_error(self, mock_get, microsoft_calendar_service, test_user):
        """Test error handling when listing Microsoft calendars."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidAuthenticationToken",
                "message": "Access token has expired"
            }
        }
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        # Mock the list_calendars method to raise an exception
        microsoft_calendar_service.list_calendars = AsyncMock(side_effect=CalendarError("Access token has expired"))

        # Attempt to list calendars
        with pytest.raises(CalendarError) as excinfo:
            await microsoft_calendar_service.list_calendars()
        
        # Verify the exception message
        assert "Access token has expired" in str(excinfo.value)

    @patch("requests.get")
    async def test_get_free_slots(self, mock_get, microsoft_calendar_service, test_user):
        """Test getting free time slots."""
        # Mock calendar response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "event1",
                    "subject": "Busy Event",
                    "start": {"dateTime": "2024-03-20T10:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-03-20T11:00:00Z", "timeZone": "UTC"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock the get_free_slots method
        free_slots_data = [
            {
                "start": datetime(2024, 3, 20, 9, 0, tzinfo=timezone.utc),
                "end": datetime(2024, 3, 20, 10, 0, tzinfo=timezone.utc)
            },
            {
                "start": datetime(2024, 3, 20, 11, 0, tzinfo=timezone.utc),
                "end": datetime(2024, 3, 20, 12, 0, tzinfo=timezone.utc)
            }
        ]
        microsoft_calendar_service.get_free_slots = AsyncMock(return_value=free_slots_data)

        # Get free slots
        start_time = datetime(2024, 3, 20, 9, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 3, 20, 17, 0, tzinfo=timezone.utc)
        duration = timedelta(hours=1)
        free_slots = await microsoft_calendar_service.get_free_slots(
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )
        
        # Assertions
        assert len(free_slots) == 2
        for slot in free_slots:
            assert slot["start"] < slot["end"]
            assert slot["end"] - slot["start"] >= duration

    @patch("requests.get")
    async def test_get_free_slots_error(self, mock_get, microsoft_calendar_service, test_user):
        """Test error handling when getting free time slots."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidAuthenticationToken",
                "message": "Access token has expired"
            }
        }
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        # Mock the get_free_slots method to raise an exception
        microsoft_calendar_service.get_free_slots = AsyncMock(side_effect=CalendarError("Access token has expired"))

        # Attempt to get free slots
        start_time = datetime(2024, 3, 20, 9, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 3, 20, 17, 0, tzinfo=timezone.utc)
        duration = timedelta(hours=1)
        with pytest.raises(CalendarError) as excinfo:
            await microsoft_calendar_service.get_free_slots(
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
        
        # Verify the exception message
        assert "Access token has expired" in str(excinfo.value) 