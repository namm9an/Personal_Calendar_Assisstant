"""
Tests for Microsoft Calendar service.
"""
import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.ms_calendar import (
    MSCalendarEvent,
    MSCalendarCreate,
    MSCalendarUpdate,
    MSFreeSlotRequest,
    MSTimeSlot,
    MSAttendee,
)
from app.services.ms_calendar import MicrosoftCalendarClient
from app.services.encryption import TokenEncryption


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_user():
    """Mock user with Microsoft credentials."""
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.microsoft_access_token = TokenEncryption.encrypt("test-access-token")
    user.microsoft_refresh_token = TokenEncryption.encrypt("test-refresh-token")
    user.microsoft_token_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return user


@pytest.fixture
def mock_token_encryption():
    """Mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption


@pytest.fixture
def calendar_client(mock_db, mock_token_encryption):
    """Create a Microsoft Calendar client with mocked dependencies."""
    with patch("app.services.ms_calendar.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.ms_calendar.settings") as mock_settings:
            mock_settings.token_encryption_key = "test-encryption-key"
            mock_settings.ms_client_id = "test-client-id"
            mock_settings.ms_client_secret = "test-client-secret"
            mock_settings.ms_tenant_id = "test-tenant-id"
            client = MicrosoftCalendarClient(mock_db)
            return client


@pytest.fixture
def mock_event_data():
    """Mock Microsoft event data."""
    return {
        "id": "test-event-id",
        "subject": "Test Event",
        "body": {
            "contentType": "text",
            "content": "Test event description"
        },
        "start": {
            "dateTime": "2023-01-01T10:00:00Z",
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": "2023-01-01T11:00:00Z",
            "timeZone": "UTC"
        },
        "location": {
            "displayName": "Test Location"
        },
        "attendees": [
            {
                "emailAddress": {
                    "address": "attendee@example.com",
                    "name": "Test Attendee"
                },
                "type": "required"
            }
        ],
        "organizer": {
            "emailAddress": {
                "address": "organizer@example.com",
                "name": "Test Organizer"
            }
        },
        "createdDateTime": "2023-01-01T09:00:00Z",
        "lastModifiedDateTime": "2023-01-01T09:00:00Z",
        "isAllDay": False,
        "webLink": "https://outlook.office.com/calendar/item/test-event-id",
    }


class TestMicrosoftCalendarClient:
    """Tests for MicrosoftCalendarClient."""

    def test_get_user_not_found(self, calendar_client, mock_db):
        """Test getting user when not found."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc_info:
            calendar_client._get_user("non-existent-user")

        # Verify
        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_refresh_token_if_needed_no_token(self, calendar_client, mock_db, mock_user):
        """Test token refresh when no token is available."""
        # Setup
        mock_user.microsoft_access_token = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Test
        with pytest.raises(HTTPException) as exc_info:
            calendar_client._refresh_token_if_needed(mock_user)

        # Verify
        assert exc_info.value.status_code == 401
        assert "Microsoft Calendar not connected" in exc_info.value.detail

    def test_refresh_token_if_needed_no_expiry(self, calendar_client, mock_db, mock_user):
        """Test token refresh when no token expiry is available."""
        # Setup
        mock_user.microsoft_token_expiry = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Test
        with pytest.raises(HTTPException) as exc_info:
            calendar_client._refresh_token_if_needed(mock_user)

        # Verify
        assert exc_info.value.status_code == 401
        assert "Microsoft Calendar not connected" in exc_info.value.detail

    def test_refresh_token_if_needed_valid_token(self, calendar_client, mock_db, mock_user, mock_token_encryption):
        """Test token refresh when token is still valid."""
        # Setup
        mock_user.microsoft_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Test
        result = calendar_client._refresh_token_if_needed(mock_user)

        # Verify
        assert result == "test-decrypted-token"
        mock_token_encryption.decrypt.assert_called_once_with("encrypted-access-token")

    @patch("app.services.ms_calendar.msal.ConfidentialClientApplication")
    def test_refresh_token_if_needed_expired_token(self, mock_msal_app, calendar_client, mock_db, mock_user):
        """Test token refresh when token is expired."""
        # Setup
        mock_user.microsoft_token_expiry = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_refresh_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600
        }

        # Test
        result = calendar_client._refresh_token_if_needed(mock_user)

        # Verify
        assert result == "new-access-token"
        mock_app_instance.acquire_token_by_refresh_token.assert_called_once()
        assert mock_user.microsoft_access_token == "encrypted-token"
        assert mock_user.microsoft_refresh_token == "encrypted-token"
        assert mock_user.microsoft_token_expiry is not None
        mock_db.commit.assert_called_once()

    @patch("app.services.ms_calendar.msal.ConfidentialClientApplication")
    def test_refresh_token_if_needed_refresh_error(self, mock_msal_app, calendar_client, mock_db, mock_user):
        """Test token refresh when refresh fails."""
        # Setup
        mock_user.microsoft_token_expiry = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_refresh_token.return_value = {
            "error": "invalid_grant",
            "error_description": "AADSTS70000: The refresh token has expired"
        }

        # Test
        with pytest.raises(HTTPException) as exc_info:
            calendar_client._refresh_token_if_needed(mock_user)

        # Verify
        assert exc_info.value.status_code == 401
        assert "Failed to refresh token" in exc_info.value.detail

    def test_format_event_from_api(self, calendar_client, mock_event_data):
        """Test formatting event from API response."""
        # Test
        result = calendar_client._format_event_from_api(mock_event_data)

        # Verify
        assert isinstance(result, MSCalendarEvent)
        assert result.id == "test-event-id"
        assert result.summary == "Test Event"
        assert result.description == "Test event description"
        assert result.location == "Test Location"
        assert result.start == datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        assert result.end == datetime.datetime(2023, 1, 1, 11, 0, 0, tzinfo=datetime.timezone.utc)
        assert result.is_all_day is False
        assert result.organizer == {"email": "organizer@example.com", "name": "Test Organizer"}
        assert len(result.attendees) == 1
        assert result.attendees[0]["email"] == "attendee@example.com"
        assert result.web_link == "https://outlook.office.com/calendar/item/test-event-id"

    def test_format_event_for_api_create(self, calendar_client):
        """Test formatting event for API create request."""
        # Setup
        event = MSCalendarCreate(
            summary="Test Event",
            description="Test Description",
            location="Test Location",
            start=datetime.datetime(2023, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2023, 1, 1, 11, 0, tzinfo=datetime.timezone.utc),
            is_all_day=False,
            attendees=[{"email": "test@example.com", "name": "Test User"}]
        )

        # Test
        result = calendar_client._format_event_for_api(event)

        # Verify
        assert result["subject"] == "Test Event"
        assert result["body"]["content"] == "Test Description"
        assert result["location"]["displayName"] == "Test Location"
        assert result["start"]["dateTime"] == "2023-01-01T10:00:00+00:00"
        assert result["end"]["dateTime"] == "2023-01-01T11:00:00+00:00"
        assert result["isAllDay"] is False
        assert len(result["attendees"]) == 1
        assert result["attendees"][0]["emailAddress"]["address"] == "test@example.com"

    def test_format_event_for_api_update(self, calendar_client):
        """Test formatting event for API update request."""
        # Setup
        event = MSCalendarUpdate(
            summary="Updated Event",
            description=None,  # Not updating description
            location="Updated Location",
            start=None,  # Not updating times
            end=None,
        )

        # Test
        result = calendar_client._format_event_for_api(event, is_update=True)

        # Verify
        assert result["subject"] == "Updated Event"
        assert "body" not in result  # Description not updated
        assert result["location"]["displayName"] == "Updated Location"
        assert "start" not in result  # Times not updated
        assert "end" not in result
        assert "isAllDay" not in result

    def test_validate_event_dates(self, calendar_client):
        """Test event date validation."""
        # Test valid dates
        start = datetime.datetime(2023, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2023, 1, 1, 11, 0, tzinfo=datetime.timezone.utc)
        calendar_client._validate_event_dates(start, end)  # Should not raise

        # Test invalid dates (end before start)
        with pytest.raises(ValueError) as exc_info:
            calendar_client._validate_event_dates(end, start)
        assert "End time must be after start time" in str(exc_info.value)

        # Test invalid dates (same time)
        with pytest.raises(ValueError) as exc_info:
            calendar_client._validate_event_dates(start, start)
        assert "End time must be after start time" in str(exc_info.value)

    @patch("app.services.ms_calendar.requests.get")
    def test_list_calendars_success(self, mock_requests_get, calendar_client, mock_db, mock_user):
        """Test listing calendars successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "calendar-1",
                    "name": "Calendar 1",
                    "canEdit": True,
                    "owner": {"name": "Test User"}
                },
                {
                    "id": "calendar-2",
                    "name": "Calendar 2",
                    "canEdit": False,
                    "owner": {"name": "Another User"}
                }
            ]
        }
        mock_requests_get.return_value = mock_response

        # Test
        result = calendar_client.list_calendars("test-user-id")

        # Verify
        assert len(result) == 2
        assert result[0]["id"] == "calendar-1"
        assert result[0]["name"] == "Calendar 1"
        assert result[0]["canEdit"] is True
        assert result[0]["owner"] == "Test User"
        mock_requests_get.assert_called_once()

    @patch("app.services.ms_calendar.requests.get")
    def test_list_calendars_api_error(self, mock_requests_get, calendar_client, mock_db, mock_user):
        """Test listing calendars with API error."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidAuthenticationToken",
                "message": "Access token has expired."
            }
        }
        mock_requests_get.return_value = mock_response

        # Test
        with pytest.raises(HTTPException) as exc_info:
            calendar_client.list_calendars("test-user-id")

        # Verify
        assert exc_info.value.status_code == 401
        assert "Authentication failed" in exc_info.value.detail
        mock_requests_get.assert_called_once()

    @patch("app.services.ms_calendar.requests.get")
    def test_list_events_success(self, mock_requests_get, calendar_client, mock_db, mock_user, mock_event_data):
        """Test listing events successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [mock_event_data]
        }
        mock_requests_get.return_value = mock_response

        time_min = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
        time_max = datetime.datetime(2023, 1, 2, tzinfo=datetime.timezone.utc)

        # Test
        result = calendar_client.list_events(
            user_id="test-user-id",
            time_min=time_min,
            time_max=time_max,
            calendar_id="primary"
        )

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], MSCalendarEvent)
        assert result[0].id == "test-event-id"
        mock_requests_get.assert_called_once()

    @patch("app.services.ms_calendar.requests.post")
    def test_create_event_success(self, mock_requests_post, calendar_client, mock_db, mock_user, mock_event_data):
        """Test creating event successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = mock_event_data
        mock_requests_post.return_value = mock_response

        event = MSCalendarCreate(
            summary="Test Event",
            description="Test Description",
            location="Test Location",
            start=datetime.datetime(2023, 1, 1, 10, 0, tzinfo=datetime.timezone.utc),
            end=datetime.datetime(2023, 1, 1, 11, 0, tzinfo=datetime.timezone.utc),
            is_all_day=False,
            attendees=[{"email": "test@example.com", "name": "Test User"}]
        )

        # Test
        result = calendar_client.create_event(
            user_id="test-user-id",
            event_create=event,
            calendar_id="primary"
        )

        # Verify
        assert isinstance(result, MSCalendarEvent)
        assert result.id == "test-event-id"
        mock_requests_post.assert_called_once()

    @patch("app.services.ms_calendar.requests.get")
    def test_get_event_success(self, mock_requests_get, calendar_client, mock_db, mock_user, mock_event_data):
        """Test getting event successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_event_data
        mock_requests_get.return_value = mock_response

        # Test
        result = calendar_client.get_event(
            user_id="test-user-id",
            event_id="test-event-id",
            calendar_id="primary"
        )

        # Verify
        assert isinstance(result, MSCalendarEvent)
        assert result.id == "test-event-id"
        mock_requests_get.assert_called_once()

    @patch("app.services.ms_calendar.requests.patch")
    def test_update_event_success(self, mock_requests_patch, calendar_client, mock_db, mock_user, mock_event_data):
        """Test updating event successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_event_data
        mock_requests_patch.return_value = mock_response

        event_update = MSCalendarUpdate(
            summary="Updated Event",
            location="Updated Location"
        )

        # Test
        result = calendar_client.update_event(
            user_id="test-user-id",
            event_id="test-event-id",
            event_update=event_update,
            calendar_id="primary"
        )

        # Verify
        assert isinstance(result, MSCalendarEvent)
        assert result.id == "test-event-id"
        mock_requests_patch.assert_called_once()

    @patch("app.services.ms_calendar.requests.delete")
    def test_delete_event_success(self, mock_requests_delete, calendar_client, mock_db, mock_user):
        """Test deleting event successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests_delete.return_value = mock_response

        # Test
        calendar_client.delete_event(
            user_id="test-user-id",
            event_id="test-event-id",
            calendar_id="primary"
        )

        # Verify
        mock_requests_delete.assert_called_once()

    @patch("app.services.ms_calendar.requests.post")
    def test_find_free_slots_success(self, mock_requests_post, calendar_client, mock_db, mock_user):
        """Test finding free slots successfully."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "scheduleId": "test@example.com",
                    "availabilityView": "000111000",  # 0 = Free, 1 = Busy
                    "scheduleItems": [
                        {
                            "status": "Busy",
                            "start": {
                                "dateTime": "2023-01-01T11:00:00Z",
                                "timeZone": "UTC"
                            },
                            "end": {
                                "dateTime": "2023-01-01T12:30:00Z",
                                "timeZone": "UTC"
                            }
                        }
                    ]
                }
            ]
        }
        mock_requests_post.return_value = mock_response

        # Test
        request = MSFreeSlotRequest(
            duration_minutes=30,
            start_date=datetime.datetime(2023, 1, 1, 9, 0, tzinfo=datetime.timezone.utc),
            end_date=datetime.datetime(2023, 1, 1, 17, 0, tzinfo=datetime.timezone.utc),
            attendees=["test@example.com"]
        )
        result = calendar_client.find_free_slots(
            user_id="test-user-id",
            request=request,
            calendar_id="primary"
        )

        # Verify
        assert isinstance(result, list)
        assert all(isinstance(slot, MSTimeSlot) for slot in result)
        assert len(result) > 0
        mock_requests_post.assert_called_once()

    def test_validate_free_slot_request(self, calendar_client):
        """Test free slot request validation."""
        # Test valid request
        request = MSFreeSlotRequest(
            duration_minutes=30,
            start_date=datetime.datetime(2023, 1, 1, 9, 0, tzinfo=datetime.timezone.utc),
            end_date=datetime.datetime(2023, 1, 1, 17, 0, tzinfo=datetime.timezone.utc)
        )
        calendar_client._validate_free_slot_request(request)  # Should not raise

        # Test invalid duration
        with pytest.raises(ValueError) as exc_info:
            request = MSFreeSlotRequest(
                duration_minutes=4,  # Less than minimum
                start_date=datetime.datetime(2023, 1, 1, 9, 0, tzinfo=datetime.timezone.utc),
                end_date=datetime.datetime(2023, 1, 1, 17, 0, tzinfo=datetime.timezone.utc)
            )
            calendar_client._validate_free_slot_request(request)
        assert "Duration must be between 5 and 480 minutes" in str(exc_info.value)

        # Test invalid date range
        with pytest.raises(ValueError) as exc_info:
            request = MSFreeSlotRequest(
                duration_minutes=30,
                start_date=datetime.datetime(2023, 1, 1, 17, 0, tzinfo=datetime.timezone.utc),
                end_date=datetime.datetime(2023, 1, 1, 9, 0, tzinfo=datetime.timezone.utc)
            )
            calendar_client._validate_free_slot_request(request)
        assert "End date must be after start date" in str(exc_info.value)
