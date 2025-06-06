from typing import List, Dict, Any
from datetime import datetime, timedelta

class GoogleCalendarService:
    async def list_events(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return [
            {
                "id": "event1",
                "summary": "Test Event 1",
                "start": {"dateTime": datetime.now().isoformat()},
                "end": {"dateTime": (datetime.now() + timedelta(hours=1)).isoformat()},
                "description": "Test Description 1",
                "location": {"displayName": "Test Location 1"},
                "attendees": [
                    {"email": "test1@example.com", "displayName": "Test User 1"}
                ]
            }
        ]

    async def find_free_slots(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return [
            {"start": datetime.now().isoformat(), "end": (datetime.now() + timedelta(hours=1)).isoformat()}
        ]

    async def create_event(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "id": "new_event",
            "summary": kwargs.get("summary", "New Event"),
            "start": {"dateTime": kwargs.get("start", datetime.now().isoformat())},
            "end": {"dateTime": kwargs.get("end", (datetime.now() + timedelta(hours=1)).isoformat())},
            "description": kwargs.get("description", ""),
            "location": {"displayName": kwargs.get("location", "")},
            "attendees": kwargs.get("attendees", [])
        }

    async def update_event(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "id": kwargs.get("event_id", "updated_event"),
            "summary": kwargs.get("summary", "Updated Event"),
            "start": {"dateTime": kwargs.get("start", datetime.now().isoformat())},
            "end": {"dateTime": kwargs.get("end", (datetime.now() + timedelta(hours=1)).isoformat())},
            "description": kwargs.get("description", ""),
            "location": {"displayName": kwargs.get("location", "")},
            "attendees": kwargs.get("attendees", [])
        }

    async def delete_event(self, *args, **kwargs) -> bool:
        return True 