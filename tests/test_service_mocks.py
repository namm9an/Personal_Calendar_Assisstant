import pytest
from datetime import datetime, timedelta
from app.schemas.tool_schemas import EventSchema
from unittest.mock import MagicMock, AsyncMock

# Test Mock Google Service
def test_mock_google_service_list_events(mock_google_service):
    now = datetime.utcnow()
    events = mock_google_service.list_events("dummy_token", "user_id", now, now + timedelta(hours=1))
    assert len(events) == 2
    assert all(isinstance(ev, dict) for ev in events)
    assert all("id" in ev and "summary" in ev and "start" in ev and "end" in ev for ev in events)

def test_mock_google_service_find_free_slots(mock_google_service):
    now = datetime.utcnow()
    slots = mock_google_service.find_free_slots("dummy_token", "user_id", 30, now, now + timedelta(days=1))
    assert len(slots) == 2
    assert all(isinstance(slot, dict) for slot in slots)
    assert all("start" in slot and "end" in slot for slot in slots)

def test_mock_google_service_create_event(mock_google_service):
    now = datetime.utcnow()
    event_data = {"summary": "Test Event", "start": now, "end": now + timedelta(hours=1)}
    event = mock_google_service.create_event("dummy_token", "user_id", event_data)
    assert isinstance(event, dict)
    assert "id" in event
    assert event["summary"] == "Test Event"

def test_mock_google_service_update_event(mock_google_service):
    now = datetime.utcnow()
    event_data = {"summary": "Updated Event", "start": now, "end": now + timedelta(hours=1)}
    event = mock_google_service.update_event("dummy_token", "user_id", "existing-event-id", event_data)
    assert isinstance(event, dict)
    assert event["summary"] == "Updated Event"

def test_mock_google_service_delete_event(mock_google_service):
    result = mock_google_service.delete_event("dummy_token", "user_id", "existing-event-id")
    assert result is True

# Test Mock Microsoft Service
def test_mock_microsoft_service_list_events(mock_microsoft_service):
    now = datetime.utcnow()
    events = mock_microsoft_service.list_events("dummy_token", "user_id", now, now + timedelta(hours=1))
    assert len(events) == 1
    assert all(isinstance(ev, dict) for ev in events)
    assert all("id" in ev and "summary" in ev and "start" in ev and "end" in ev for ev in events)

def test_mock_microsoft_service_find_free_slots(mock_microsoft_service):
    now = datetime.utcnow()
    slots = mock_microsoft_service.find_free_slots("dummy_token", "user_id", 30, now, now + timedelta(days=1))
    assert len(slots) == 1
    assert all(isinstance(slot, dict) for slot in slots)
    assert all("start" in slot and "end" in slot for slot in slots)

def test_mock_microsoft_service_create_event(mock_microsoft_service):
    now = datetime.utcnow()
    event_data = {"summary": "Test MS Event", "start": now, "end": now + timedelta(hours=1)}
    event = mock_microsoft_service.create_event("dummy_token", "user_id", event_data)
    assert isinstance(event, dict)
    assert "id" in event
    assert event["summary"] == "Test MS Event"

def test_mock_microsoft_service_update_event(mock_microsoft_service):
    now = datetime.utcnow()
    event_data = {"summary": "Updated MS Event", "start": now, "end": now + timedelta(hours=1)}
    event = mock_microsoft_service.update_event("dummy_token", "user_id", "existing-event-id", event_data)
    assert isinstance(event, dict)
    assert event["summary"] == "Updated MS Event"

def test_mock_microsoft_service_delete_event(mock_microsoft_service):
    result = mock_microsoft_service.delete_event("dummy_token", "user_id", "existing-event-id")
    assert result is True

class MockGoogleService:
    def __init__(self):
        self.list_events = AsyncMock(return_value=[])
        self.find_free_slots = AsyncMock(return_value=[])
        self.create_event = AsyncMock(return_value={"id": "mock_event_id"})
        self.update_event = AsyncMock(return_value={"id": "mock_event_id"})
        self.delete_event = AsyncMock(return_value=True)

    async def __call__(self, *args, **kwargs):
        return self

class MockMicrosoftService:
    def __init__(self):
        self.list_events = AsyncMock(return_value=[])
        self.find_free_slots = AsyncMock(return_value=[])
        self.create_event = AsyncMock(return_value={"id": "mock_event_id"})
        self.update_event = AsyncMock(return_value={"id": "mock_event_id"})
        self.delete_event = AsyncMock(return_value=True)

    async def __call__(self, *args, **kwargs):
        return self

@pytest.fixture
def mock_google_service():
    return MockGoogleService()

@pytest.fixture
def mock_microsoft_service():
    return MockMicrosoftService() 