import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, call, AsyncMock
from datetime import datetime, timedelta, timezone
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
    cancel_event_tool,
    _map_service_event_to_tool_event
)
from src.tool_schemas import (
    ListEventsInput, ListEventsOutput,
    FreeSlotsInput, FreeSlotsOutput,
    CreateEventInput, CreateEventOutput,
    RescheduleEventInput, RescheduleEventOutput,
    CancelEventInput, CancelEventOutput,
    EventSchema, AttendeeSchema,
    DeleteEventInput,
    UpdateEventInput
)

# Shared fixtures
@pytest.fixture
def mock_calendar_service():
    return AsyncMock()

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
    @pytest.mark.asyncio
    async def test_create_event_success(self, create_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'summary': 'Test Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().insert().execute.return_value = {'id': '123'}

        # Act
        result = await create_event_wrapper.execute(event_data)

        # Assert
        assert result == {'id': '123'}
        mock_calendar_service.events().insert.assert_has_calls([
            call(calendarId='primary', body=event_data),
            call().execute()
        ])

    @pytest.mark.asyncio
    async def test_create_event_validation_error(self, create_event_wrapper):
        # Arrange
        invalid_event_data = {'summary': 'Test Event'}  # Missing required fields

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await create_event_wrapper.execute(invalid_event_data)
        assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_event_api_error(self, create_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'summary': 'Test Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().insert().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await create_event_wrapper.execute(event_data)
        assert "Failed to create event" in str(exc_info.value)

# Test ListEventsWrapper
class TestListEventsWrapper:
    @pytest.mark.asyncio
    async def test_list_events_success(self, list_events_wrapper, mock_calendar_service):
        # Arrange
        mock_events = {
            'items': [
                {'id': '1', 'summary': 'Event 1'},
                {'id': '2', 'summary': 'Event 2'}
            ]
        }
        mock_calendar_service.events().list().execute.return_value = mock_events

        # Act
        result = await list_events_wrapper.execute({'timeMin': '2024-03-20T00:00:00Z'})

        # Assert
        assert result == mock_events
        mock_calendar_service.events().list.assert_has_calls([
            call(calendarId='primary', timeMin='2024-03-20T00:00:00Z', maxResults=10, singleEvents=True, orderBy='startTime'),
            call().execute()
        ])

    @pytest.mark.asyncio
    async def test_list_events_validation_error(self, list_events_wrapper):
        # Arrange
        invalid_params = {}  # Missing required timeMin

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await list_events_wrapper.execute(invalid_params)
        assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_events_api_error(self, list_events_wrapper, mock_calendar_service):
        # Arrange
        mock_calendar_service.events().list().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await list_events_wrapper.execute({'timeMin': '2024-03-20T00:00:00Z'})
        assert "Failed to list events" in str(exc_info.value)

# Test UpdateEventWrapper
class TestUpdateEventWrapper:
    @pytest.mark.asyncio
    async def test_update_event_success(self, update_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {
            'eventId': '123',
            'summary': 'Updated Event',
            'start': {'dateTime': '2024-03-20T10:00:00'},
            'end': {'dateTime': '2024-03-20T11:00:00'}
        }
        mock_calendar_service.events().update().execute.return_value = {'id': '123'}

        # Act
        result = await update_event_wrapper.execute(event_data)

        # Assert
        assert result == {'id': '123'}
        mock_calendar_service.events().update.assert_has_calls([
            call(calendarId='primary', eventId='123', body=event_data),
            call().execute()
        ])

    @pytest.mark.asyncio
    async def test_update_event_validation_error(self, update_event_wrapper):
        # Arrange
        invalid_event_data = {'summary': 'Updated Event'}  # Missing eventId

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await update_event_wrapper.execute(invalid_event_data)
        assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_event_api_error(self, update_event_wrapper, mock_calendar_service):
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
            await update_event_wrapper.execute(event_data)
        assert "Failed to update event" in str(exc_info.value)

# Test DeleteEventWrapper
class TestDeleteEventWrapper:
    @pytest.mark.asyncio
    async def test_delete_event_success(self, delete_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {'eventId': '123'}
        mock_calendar_service.events().delete().execute.return_value = None

        # Act
        result = await delete_event_wrapper.execute(event_data)

        # Assert
        assert result == {'status': 'success'}
        mock_calendar_service.events().delete.assert_has_calls([
            call(calendarId='primary', eventId='123'),
            call().execute()
        ])

    @pytest.mark.asyncio
    async def test_delete_event_validation_error(self, delete_event_wrapper):
        # Arrange
        invalid_event_data = {}  # Missing eventId

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await delete_event_wrapper.execute(invalid_event_data)
        assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_event_api_error(self, delete_event_wrapper, mock_calendar_service):
        # Arrange
        event_data = {'eventId': '123'}
        mock_calendar_service.events().delete().execute.side_effect = Exception("API Error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await delete_event_wrapper.execute(event_data)
        assert "Failed to delete event" in str(exc_info.value)

# Test Event Mapping
class TestEventMapping:
    def test_map_google_event(self):
        # Arrange
        google_event = {
            'id': '123',
            'summary': 'Test Event',
            'start': {'dateTime': '2024-03-20T10:00:00Z'},
            'end': {'dateTime': '2024-03-20T11:00:00Z'},
            'description': 'Test Description',
            'location': 'Test Location',
            'attendees': [
                {'email': 'test@example.com', 'displayName': 'Test User'}
            ],
            'htmlLink': 'https://calendar.google.com/event?id=123'
        }

        # Act
        result = _map_service_event_to_tool_event(google_event)

        # Assert
        assert isinstance(result, EventSchema)
        assert result.id == '123'
        assert result.summary == 'Test Event'
        assert result.start == '2024-03-20T10:00:00Z'
        assert result.end == '2024-03-20T11:00:00Z'
        assert result.description == 'Test Description'
        assert result.location == 'Test Location'
        assert len(result.attendees) == 1
        assert result.attendees[0].email == 'test@example.com'
        assert result.attendees[0].name == 'Test User'
        assert result.html_link == 'https://calendar.google.com/event?id=123'

    def test_map_microsoft_event(self):
        # Arrange
        ms_event = {
            'id': '123',
            'subject': 'Test Event',
            'start': {'dateTime': '2024-03-20T10:00:00Z', 'timeZone': 'UTC'},
            'end': {'dateTime': '2024-03-20T11:00:00Z', 'timeZone': 'UTC'},
            'bodyPreview': 'Test Description',
            'location': {'displayName': 'Test Location'},
            'attendees': [
                {'emailAddress': {'address': 'test@example.com', 'name': 'Test User'}}
            ],
            'webLink': 'https://outlook.office.com/calendar/item/123'
        }

        # Act
        result = _map_service_event_to_tool_event(ms_event)

        # Assert
        assert isinstance(result, EventSchema)
        assert result.id == '123'
        assert result.summary == 'Test Event'
        assert result.start == '2024-03-20T10:00:00Z'
        assert result.end == '2024-03-20T11:00:00Z'
        assert result.description == 'Test Description'
        assert result.location == 'Test Location'
        assert len(result.attendees) == 1
        assert result.attendees[0].email == 'test@example.com'
        assert result.attendees[0].name == 'Test User'
        assert result.html_link == 'https://outlook.office.com/calendar/item/123'

# Test ListEventsTool
class TestListEventsTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = ListEventsInput(
            provider="google",
            user_id="u1",
            start_time=now,
            end_time=now + timedelta(days=1)
        )

        # Act
        output = await list_events_tool(input)

        # Assert
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) > 0
        assert isinstance(output.events[0], EventSchema)

    @pytest.mark.asyncio
    async def test_microsoft_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = ListEventsInput(
            provider="microsoft",
            user_id="u1",
            start_time=now,
            end_time=now + timedelta(days=1)
        )

        # Act
        output = await list_events_tool(input)

        # Assert
        assert isinstance(output, ListEventsOutput)
        assert len(output.events) > 0
        assert isinstance(output.events[0], EventSchema)

    @pytest.mark.asyncio
    async def test_unknown_provider(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = ListEventsInput(
            provider="other",
            user_id="u1",
            start_time=now,
            end_time=now + timedelta(days=1)
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await list_events_tool(input)
        assert "Unsupported provider" in str(exc_info.value)

# Test FindFreeSlotsTool
class TestFindFreeSlotsTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = FreeSlotsInput(
            provider="google",
            user_id="u1",
            duration_minutes=30,
            range_start=now,
            range_end=now + timedelta(days=1)
        )

        # Act
        output = await find_free_slots_tool(input)

        # Assert
        assert isinstance(output, FreeSlotsOutput)
        assert len(output.slots) > 0

    @pytest.mark.asyncio
    async def test_microsoft_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = FreeSlotsInput(
            provider="microsoft",
            user_id="u1",
            duration_minutes=30,
            range_start=now,
            range_end=now + timedelta(days=1)
        )

        # Act
        output = await find_free_slots_tool(input)

        # Assert
        assert isinstance(output, FreeSlotsOutput)
        assert len(output.slots) > 0

    @pytest.mark.asyncio
    async def test_invalid_duration(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = FreeSlotsInput(
            provider="google",
            user_id="u1",
            duration_minutes=0,  # Invalid duration
            range_start=now,
            range_end=now + timedelta(days=1)
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await find_free_slots_tool(input)
        assert "Duration must be positive" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unknown_provider(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = FreeSlotsInput(
            provider="other",
            user_id="u1",
            duration_minutes=30,
            range_start=now,
            range_end=now + timedelta(days=1)
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await find_free_slots_tool(input)
        assert "Unsupported provider" in str(exc_info.value)

# Test CreateEventTool
class TestCreateEventTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = CreateEventInput(
            provider="google",
            user_id="u1",
            summary="Test Event",
            start=now,
            end=now + timedelta(hours=1),
            description="Test Description",
            location="Test Location",
            attendees=[
                AttendeeSchema(email="test@example.com", name="Test User")
            ]
        )

        # Act
        output = await create_event_tool(input)

        # Assert
        assert isinstance(output, CreateEventOutput)
        assert isinstance(output.event, EventSchema)
        assert output.event.summary == "Test Event"

    @pytest.mark.asyncio
    async def test_microsoft_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = CreateEventInput(
            provider="microsoft",
            user_id="u1",
            summary="Test Event",
            start=now,
            end=now + timedelta(hours=1),
            description="Test Description",
            location="Test Location",
            attendees=[
                AttendeeSchema(email="test@example.com", name="Test User")
            ]
        )

        # Act
        output = await create_event_tool(input)

        # Assert
        assert isinstance(output, CreateEventOutput)
        assert isinstance(output.event, EventSchema)
        assert output.event.summary == "Test Event"

    @pytest.mark.asyncio
    async def test_invalid_dates(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = CreateEventInput(
            provider="google",
            user_id="u1",
            summary="Test Event",
            start=now + timedelta(hours=1),  # Start after end
            end=now,
            description="Test Description"
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await create_event_tool(input)
        assert "End time must be after start time" in str(exc_info.value)

# Test UpdateEventTool
class TestUpdateEventTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = UpdateEventInput(
            provider="google",
            user_id="u1",
            event_id="event1",
            summary="Updated Event",
            start=now,
            end=now + timedelta(hours=1),
            description="Updated Description",
            location="Updated Location"
        )

        # Act
        output = await update_event_tool(input)

        # Assert
        assert isinstance(output, UpdateEventOutput)
        assert isinstance(output.event, EventSchema)
        assert output.event.summary == "Updated Event"

    @pytest.mark.asyncio
    async def test_microsoft_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = UpdateEventInput(
            provider="microsoft",
            user_id="u1",
            event_id="event1",
            summary="Updated Event",
            start=now,
            end=now + timedelta(hours=1),
            description="Updated Description",
            location="Updated Location"
        )

        # Act
        output = await update_event_tool(input)

        # Assert
        assert isinstance(output, UpdateEventOutput)
        assert isinstance(output.event, EventSchema)
        assert output.event.summary == "Updated Event"

    @pytest.mark.asyncio
    async def test_invalid_dates(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = UpdateEventInput(
            provider="google",
            user_id="u1",
            event_id="event1",
            summary="Updated Event",
            start=now + timedelta(hours=1),  # Start after end
            end=now,
            description="Updated Description"
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await update_event_tool(input)
        assert "End time must be after start time" in str(exc_info.value)

# Test DeleteEventTool
class TestDeleteEventTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        input = DeleteEventInput(
            provider="google",
            user_id="u1",
            event_id="event1"
        )

        # Act
        output = await delete_event_tool(input)

        # Assert
        assert isinstance(output, DeleteEventOutput)
        assert output.success is True

    @pytest.mark.asyncio
    async def test_microsoft_success(self):
        # Arrange
        input = DeleteEventInput(
            provider="microsoft",
            user_id="u1",
            event_id="event1"
        )

        # Act
        output = await delete_event_tool(input)

        # Assert
        assert isinstance(output, DeleteEventOutput)
        assert output.success is True

# Test RescheduleEventTool
class TestRescheduleEventTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = RescheduleEventInput(
            provider="google",
            user_id="u1",
            event_id="event1",
            new_start=now,
            new_end=now + timedelta(hours=1)
        )

        # Act
        output = await reschedule_event_tool(input)

        # Assert
        assert isinstance(output, RescheduleEventOutput)
        assert isinstance(output.event, EventSchema)

    @pytest.mark.asyncio
    async def test_microsoft_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = RescheduleEventInput(
            provider="microsoft",
            user_id="u1",
            event_id="event1",
            new_start=now,
            new_end=now + timedelta(hours=1)
        )

        # Act
        output = await reschedule_event_tool(input)

        # Assert
        assert isinstance(output, RescheduleEventOutput)
        assert isinstance(output.event, EventSchema)

    @pytest.mark.asyncio
    async def test_invalid_dates(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = RescheduleEventInput(
            provider="google",
            user_id="u1",
            event_id="event1",
            new_start=now + timedelta(hours=1),  # Start after end
            new_end=now
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await reschedule_event_tool(input)
        assert "New end time must be after new start time" in str(exc_info.value)

# Test CancelEventTool
class TestCancelEventTool:
    @pytest.mark.asyncio
    async def test_google_success(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = CancelEventInput(
            provider="google",
            user_id="u1",
            event_id="event1",
            start=now,
            end=now + timedelta(hours=1)
        )

        # Act
        output = await cancel_event_tool(input)

        # Assert
        assert isinstance(output, CancelEventOutput)
        assert output.success is True

    @pytest.mark.asyncio
    async def test_unknown_provider(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = CancelEventInput(
            provider="other",
            user_id="u1",
            event_id="event1",
            start=now,
            end=now + timedelta(hours=1)
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await cancel_event_tool(input)
        assert "Unsupported provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_dates(self):
        # Arrange
        now = datetime.now(timezone.utc)
        input = CancelEventInput(
            provider="google",
            user_id="u1",
            event_id="event1",
            start=now + timedelta(hours=1),  # Start after end
            end=now
        )

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            await cancel_event_tool(input)
        assert "End time must be after start time" in str(exc_info.value) 