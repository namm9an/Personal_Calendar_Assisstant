import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta
from src.calendar_tool_wrappers import (
    CreateEventWrapper,
    ListEventsWrapper,
    UpdateEventWrapper,
    DeleteEventWrapper,
    ToolExecutionError,
    list_events_tool,
    find_free_slots_tool,
    create_event_tool,
    reschedule_event_tool,
    cancel_event_tool
)
from src.tool_schemas import (
    ListEventsInput, ListEventsOutput,
    FreeSlotsInput, FreeSlotsOutput,
    CreateEventInput, CreateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput,
    EventSchema, AttendeeSchema
)

# Shared fixtures
@pytest.fixture
def mock_calendar_service():
    return Mock()

@pytest.fixture
def create_event_wrapper(mock_calendar_service):
    return CreateEventWrapper(mock_calendar_service)

@pytest.fixture
def list_events_wrapper(mock_calendar_service):
    return ListEventsWrapper(mock_calendar_service)

@pytest.fixture
def update_event_wrapper(mock_calendar_service):
    return UpdateEventWrapper(mock_calendar_service)

@pytest.fixture
def delete_event_wrapper(mock_calendar_service):
    return DeleteEventWrapper(mock_calendar_service)

# Test CreateEventWrapper
class TestCreateEventWrapper:
    def test_create_event_success(self, create_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'summary': 'Test Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().insert().execute.return_value = {'id': '123'}

        # Act
        result = create_event_wrapper.execute(event_data)

        # Assert
        assert result == {'id': '123'}
        mock_calendar_service.events().insert.assert_has_calls([
            call(calendarId='primary', body=event_data),
            call().execute()
        ])

    def test_create_event_validation_error(self, create_event_wrapper):
        # Arrange
        invalid_event_data = {'summary': 'Test Event'}  # Missing required fields

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            create_event_wrapper.execute(invalid_event_data)
        assert "Missing required fields" in str(exc_info.value)

    def test_create_event_api_error(self, create_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'summary': 'Test Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().insert().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            create_event_wrapper.execute(event_data)
        assert "Failed to create event" in str(exc_info.value)

# Test ListEventsWrapper
class TestListEventsWrapper:
    def test_list_events_success(self, list_events_wrapper, mock_calendar_service):
        # Arrange
        mock_events = {
            'items': [
                {'id': '1', 'summary': 'Event 1'},
                {'id': '2', 'summary': 'Event 2'}
            ]
        }
        mock_calendar_service.events().list().execute.return_value = mock_events

        # Act
        result = list_events_wrapper.execute({'timeMin': '2024-03-20T00:00:00Z'})

        # Assert
        assert result == mock_events
        mock_calendar_service.events().list.assert_has_calls([
            call(calendarId='primary', timeMin='2024-03-20T00:00:00Z', maxResults=10, singleEvents=True, orderBy='startTime'),
            call().execute()
        ])

    def test_list_events_validation_error(self, list_events_wrapper):
        # Arrange
        invalid_params = {}  # Missing required timeMin

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            list_events_wrapper.execute(invalid_params)
        assert "Missing required fields" in str(exc_info.value)

    def test_list_events_api_error(self, list_events_wrapper, mock_calendar_service):
        # Arrange
        mock_calendar_service.events().list().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            list_events_wrapper.execute({'timeMin': '2024-03-20T00:00:00Z'})
        assert "Failed to list events" in str(exc_info.value)

# Test UpdateEventWrapper
class TestUpdateEventWrapper:
    def test_update_event_success(self, update_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'eventId': '123',
            'summary': 'Updated Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().update().execute.return_value = {'id': '123'}

        # Act
        result = update_event_wrapper.execute(event_data)

        # Assert
        assert result == {'id': '123'}
        mock_calendar_service.events().update.assert_has_calls([
            call(calendarId='primary', eventId='123', body=event_data),
            call().execute()
        ])

    def test_update_event_validation_error(self, update_event_wrapper):
        # Arrange
        invalid_event_data = {'summary': 'Updated Event'}  # Missing eventId

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            update_event_wrapper.execute(invalid_event_data)
        assert "Missing required fields" in str(exc_info.value)

    def test_update_event_api_error(self, update_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'eventId': '123',
            'summary': 'Updated Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().update().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            update_event_wrapper.execute(event_data)
        assert "Failed to update event" in str(exc_info.value)

# Test DeleteEventWrapper
class TestDeleteEventWrapper:
    def test_delete_event_success(self, delete_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {'eventId': '123'}
        mock_calendar_service.events().delete().execute.return_value = None

        # Act
        result = delete_event_wrapper.execute(event_data)

        # Assert
        assert result == {'status': 'success'}
        mock_calendar_service.events().delete.assert_has_calls([
            call(calendarId='primary', eventId='123'),
            call().execute()
        ])

    def test_delete_event_validation_error(self, delete_event_wrapper):
        # Arrange
        invalid_event_data = {}  # Missing eventId

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            delete_event_wrapper.execute(invalid_event_data)
        assert "Missing required fields" in str(exc_info.value)

    def test_delete_event_api_error(self, delete_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {'eventId': '123'}
        mock_calendar_service.events().delete().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            delete_event_wrapper.execute(event_data)
        assert "Failed to delete event" in str(exc_info.value)

# --- New tool wrapper tests ---
class TestListEventsTool:
    def test_google_success(self):
        now = datetime.utcnow()
        input = ListEventsInput(provider="google", user_id="u1", start=now, end=now+timedelta(hours=1))
        output = list_events_tool(input)
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 2
        assert all(isinstance(ev, EventSchema) for ev in output.events)

    def test_microsoft_success(self):
        now = datetime.utcnow()
        input = ListEventsInput(provider="microsoft", user_id="u1", start=now, end=now+timedelta(hours=1))
        output = list_events_tool(input)
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) == 1
        assert all(isinstance(ev, EventSchema) for ev in output.events)

    def test_unknown_provider(self):
        now = datetime.utcnow()
        input = ListEventsInput(provider="other", user_id="u1", start=now, end=now+timedelta(hours=1))
        with pytest.raises(ToolExecutionError):
            list_events_tool(input)

class TestFindFreeSlotsTool:
    def test_google_success(self):
        now = datetime.utcnow()
        input = FreeSlotsInput(provider="google", user_id="u1", duration_minutes=30, range_start=now, range_end=now+timedelta(days=1))
        output = find_free_slots_tool(input)
        assert isinstance(output, FreeSlotsOutput)
        assert len(output.slots) == 2

    def test_microsoft_success(self):
        now = datetime.utcnow()
        input = FreeSlotsInput(provider="microsoft", user_id="u1", duration_minutes=30, range_start=now, range_end=now+timedelta(days=1))
        output = find_free_slots_tool(input)
        assert isinstance(output, FreeSlotsOutput)
        assert len(output.slots) == 2

    def test_invalid_duration(self):
        now = datetime.utcnow()
        with pytest.raises(Exception):
            FreeSlotsInput(provider="google", user_id="u1", duration_minutes=-10, range_start=now, range_end=now+timedelta(days=1))

    def test_unknown_provider(self):
        now = datetime.utcnow()
        input = FreeSlotsInput(provider="other", user_id="u1", duration_minutes=30, range_start=now, range_end=now+timedelta(days=1))
        with pytest.raises(ToolExecutionError):
            find_free_slots_tool(input)

class TestCreateEventTool:
    def test_google_success(self):
        now = datetime.utcnow()
        input = CreateEventInput(
            provider="google",
            user_id="u1",
            summary="Team Meeting",
            start=now+timedelta(hours=2),
            end=now+timedelta(hours=3),
            description="Discuss Q2 goals",
            location="Conference Room A",
            attendees=[AttendeeSchema(email="alice@example.com")],
        )
        output = create_event_tool(input)
        assert isinstance(output, CreateEventOutput)
        assert isinstance(output.event, EventSchema)

    def test_missing_summary(self):
        now = datetime.utcnow()
        with pytest.raises(Exception):
            CreateEventInput(
                provider="google",
                user_id="u1",
                summary=None,
                start=now+timedelta(hours=2),
                end=now+timedelta(hours=3),
            )

    def test_unknown_provider(self):
        now = datetime.utcnow()
        input = CreateEventInput(
            provider="other",
            user_id="u1",
            summary="Team Meeting",
            start=now+timedelta(hours=2),
            end=now+timedelta(hours=3),
        )
        # The stub does not raise for provider, but you can add this if you want stricter logic

class TestRescheduleEventTool:
    def test_google_success(self):
        now = datetime.utcnow()
        input = RescheduleEventInput(
            provider="google",
            user_id="u1",
            event_id="e1",
            new_start=now+timedelta(days=1, hours=4),
        )
        output = reschedule_event_tool(input)
        assert isinstance(output, RescheduleEventOutput)
        assert output.event.start == input.new_start

    def test_unknown_provider(self):
        now = datetime.utcnow()
        input = RescheduleEventInput(
            provider="other",
            user_id="u1",
            event_id="e1",
            new_start=now+timedelta(days=1, hours=4),
        )
        with pytest.raises(ToolExecutionError):
            reschedule_event_tool(input)

class TestCancelEventTool:
    def test_google_success(self):
        input = CancelEventInput(provider="google", user_id="u1", event_id="e1")
        output = cancel_event_tool(input)
        assert isinstance(output, CancelEventOutput)
        assert output.success is True

    def test_unknown_provider(self):
        input = CancelEventInput(provider="other", user_id="u1", event_id="e1")
        with pytest.raises(ToolExecutionError):
            cancel_event_tool(input) 