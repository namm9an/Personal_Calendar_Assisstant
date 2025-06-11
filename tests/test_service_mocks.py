import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from app.schemas.tool_schemas import EventSchema
from unittest.mock import MagicMock, AsyncMock

# Test Mock Google Service
@pytest.mark.asyncio
async def test_mock_google_service_list_events(mock_google_service):
    now = datetime.utcnow()
    events = await mock_google_service.list_events(time_min=now, time_max=now + timedelta(hours=1))
    assert len(events) == 2
    assert all(isinstance(ev, dict) for ev in events)
    assert all("id" in ev and "summary" in ev and "start" in ev and "end" in ev for ev in events)

@pytest.mark.asyncio
async def test_mock_google_service_find_free_slots(mock_google_service):
    now = datetime.utcnow()
    slots = await mock_google_service.find_free_slots(start_time=now, end_time=now + timedelta(days=1), duration_minutes=30)
    assert len(slots) == 2
    assert all(isinstance(slot, dict) for slot in slots)
    assert all("start" in slot and "end" in slot for slot in slots)

@pytest.mark.asyncio
async def test_mock_google_service_create_event(mock_google_service):
    now = datetime.utcnow()
    event_data = {"summary": "Test Event", "start": now, "end": now + timedelta(hours=1)}
    event = await mock_google_service.create_event(event_data=event_data)
    assert isinstance(event, dict)
    assert "id" in event
    assert event["summary"] == "Test Event"

@pytest.mark.asyncio
async def test_mock_google_service_update_event(mock_google_service):
    now = datetime.utcnow()
    event_data = {"summary": "Updated Event", "start": now, "end": now + timedelta(hours=1)}
    event = await mock_google_service.update_event(event_id="existing-event-id", event_data=event_data)
    assert isinstance(event, dict)
    assert event["summary"] == "Updated Event"

@pytest.mark.asyncio
async def test_mock_google_service_delete_event(mock_google_service):
    result = await mock_google_service.delete_event(event_id="existing-event-id")
    assert result is True

# Test Mock Microsoft Service
@pytest.mark.asyncio
async def test_mock_microsoft_service_list_events(mock_microsoft_service):
    now = datetime.utcnow()
    events = await mock_microsoft_service.list_events(time_min=now, time_max=now + timedelta(hours=1))
    assert len(events) == 1
    assert all(isinstance(ev, dict) for ev in events)
    assert all("id" in ev and "summary" in ev and "start" in ev and "end" in ev for ev in events)

@pytest.mark.asyncio
async def test_mock_microsoft_service_find_free_slots(mock_microsoft_service):
    now = datetime.utcnow()
    slots = await mock_microsoft_service.find_free_slots(start_time=now, end_time=now + timedelta(days=1), duration_minutes=30)
    assert len(slots) == 1
    assert all(isinstance(slot, dict) for slot in slots)
    assert all("start" in slot and "end" in slot for slot in slots)

@pytest.mark.asyncio
async def test_mock_microsoft_service_create_event(mock_microsoft_service):
    now = datetime.utcnow()
    event_data = {"summary": "Test MS Event", "start": now, "end": now + timedelta(hours=1)}
    event = await mock_microsoft_service.create_event(event_data=event_data)
    assert isinstance(event, dict)
    assert "id" in event
    assert event["summary"] == "Test MS Event"

@pytest.mark.asyncio
async def test_mock_microsoft_service_update_event(mock_microsoft_service):
    now = datetime.utcnow()
    event_data = {"summary": "Updated MS Event", "start": now, "end": now + timedelta(hours=1)}
    event = await mock_microsoft_service.update_event(event_id="existing-event-id", event_data=event_data)
    assert isinstance(event, dict)
    assert event["summary"] == "Updated MS Event"

@pytest.mark.asyncio
async def test_mock_microsoft_service_delete_event(mock_microsoft_service):
    result = await mock_microsoft_service.delete_event(event_id="existing-event-id")
    assert result is True

class MockGoogleService:
    def __init__(self):
        pass
        
    async def list_events(self, time_min=None, time_max=None, calendar_id="primary", max_results=10):
        """Return a list of events"""
        return [
            {
                "id": "test-event-1",
                "summary": "Test Event 1",
                "start": time_min,
                "end": time_min + timedelta(hours=1)
            },
            {
                "id": "test-event-2",
                "summary": "Test Event 2",
                "start": time_max - timedelta(hours=1),
                "end": time_max
            }
        ]
        
    async def find_free_slots(self, start_time, end_time, duration_minutes=30, calendar_id="primary"):
        """Return a list of free time slots"""
        return [
            {
                "start": start_time,
                "end": start_time + timedelta(minutes=duration_minutes)
            },
            {
                "start": end_time - timedelta(minutes=duration_minutes),
                "end": end_time
            }
        ]
        
    async def create_event(self, event_data, calendar_id="primary"):
        """Create an event"""
        return {
            "id": "new-test-event-id",
            "summary": event_data.get("summary", "New Event"),
            "start": event_data.get("start"),
            "end": event_data.get("end")
        }
        
    async def update_event(self, event_id, event_data, calendar_id="primary"):
        """Update an event"""
        return {
            "id": event_id,
            "summary": event_data.get("summary", "Updated Event"),
            "start": event_data.get("start"),
            "end": event_data.get("end")
        }
        
    async def delete_event(self, event_id, calendar_id="primary"):
        """Delete an event"""
        return True

class MockMicrosoftService:
    def __init__(self):
        pass
        
    async def list_events(self, time_min=None, time_max=None, calendar_id="primary", max_results=10):
        """Return a list of events"""
        return [
            {
                "id": "ms-test-event-1",
                "summary": "MS Test Event 1",
                "start": time_min,
                "end": time_max
            }
        ]
        
    async def find_free_slots(self, start_time, end_time, duration_minutes=30, calendar_id="primary"):
        """Return a list of free time slots"""
        return [
            {
                "start": start_time,
                "end": start_time + timedelta(minutes=duration_minutes)
            }
        ]
        
    async def create_event(self, event_data, calendar_id="primary"):
        """Create an event"""
        return {
            "id": "new-ms-test-event-id",
            "summary": event_data.get("summary", "New MS Event"),
            "start": event_data.get("start"),
            "end": event_data.get("end")
        }
        
    async def update_event(self, event_id, event_data, calendar_id="primary"):
        """Update an event"""
        return {
            "id": event_id,
            "summary": event_data.get("summary", "Updated MS Event"),
            "start": event_data.get("start"),
            "end": event_data.get("end")
        }
        
    async def delete_event(self, event_id, calendar_id="primary"):
        """Delete an event"""
        return True

@pytest.fixture
def mock_google_service():
    return MockGoogleService()

@pytest.fixture
def mock_microsoft_service():
    return MockMicrosoftService() 