from datetime import datetime, timedelta
from typing import List, Dict, Any

class MockGoogleCalendarService:
    def list_events(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return [
            {
                "id": "event1",
                "summary": "Test Event 1",
                "start": {"dateTime": "2023-01-01T10:00:00"},
                "end": {"dateTime": "2023-01-01T11:00:00"},
                "description": "Test Description 1",
                "location": {"displayName": "Test Location 1"},
                "attendees": [
                    {"email": "test1@example.com", "displayName": "Test User 1"}
                ]
            },
            {
                "id": "event2",
                "summary": "Test Event 2",
                "start": {"dateTime": "2023-01-02T10:00:00"},
                "end": {"dateTime": "2023-01-02T11:00:00"},
                "description": "Test Description 2",
                "location": {"displayName": "Test Location 2"},
                "attendees": [
                    {"email": "test2@example.com", "displayName": "Test User 2"}
                ]
            }
        ]

    def create_event(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "id": "new_event",
            "summary": kwargs.get("summary", "New Event"),
            "start": {"dateTime": kwargs.get("start", datetime.now().isoformat())},
            "end": {"dateTime": kwargs.get("end", (datetime.now() + timedelta(hours=1)).isoformat())},
            "description": kwargs.get("description", ""),
            "location": {"displayName": kwargs.get("location", "")},
            "attendees": kwargs.get("attendees", [])
        }

    def update_event(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "id": kwargs.get("event_id", "updated_event"),
            "summary": kwargs.get("summary", "Updated Event"),
            "start": {"dateTime": kwargs.get("start", datetime.now().isoformat())},
            "end": {"dateTime": kwargs.get("end", (datetime.now() + timedelta(hours=1)).isoformat())},
            "description": kwargs.get("description", ""),
            "location": {"displayName": kwargs.get("location", "")},
            "attendees": kwargs.get("attendees", [])
        }

    def delete_event(self, *args, **kwargs) -> bool:
        return True

class MockMicrosoftCalendarService:
    def list_events(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return [
            {
                "id": "event1",
                "subject": "Test Event 1",
                "start": {"dateTime": "2023-01-01T10:00:00"},
                "end": {"dateTime": "2023-01-01T11:00:00"},
                "body": {"content": "Test Description 1"},
                "location": {"displayName": "Test Location 1"},
                "attendees": [
                    {"emailAddress": {"address": "test1@example.com", "name": "Test User 1"}}
                ]
            },
            {
                "id": "event2",
                "subject": "Test Event 2",
                "start": {"dateTime": "2023-01-02T10:00:00"},
                "end": {"dateTime": "2023-01-02T11:00:00"},
                "body": {"content": "Test Description 2"},
                "location": {"displayName": "Test Location 2"},
                "attendees": [
                    {"emailAddress": {"address": "test2@example.com", "name": "Test User 2"}}
                ]
            }
        ]

    def create_event(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "id": "new_event",
            "subject": kwargs.get("summary", "New Event"),
            "start": {"dateTime": kwargs.get("start", datetime.now().isoformat())},
            "end": {"dateTime": kwargs.get("end", (datetime.now() + timedelta(hours=1)).isoformat())},
            "body": {"content": kwargs.get("description", "")},
            "location": {"displayName": kwargs.get("location", "")},
            "attendees": [
                {"emailAddress": {"address": a["email"], "name": a.get("name", "")}}
                for a in kwargs.get("attendees", [])
            ]
        }

    def update_event(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "id": kwargs.get("event_id", "updated_event"),
            "subject": kwargs.get("summary", "Updated Event"),
            "start": {"dateTime": kwargs.get("start", datetime.now().isoformat())},
            "end": {"dateTime": kwargs.get("end", (datetime.now() + timedelta(hours=1)).isoformat())},
            "body": {"content": kwargs.get("description", "")},
            "location": {"displayName": kwargs.get("location", "")},
            "attendees": [
                {"emailAddress": {"address": a["email"], "name": a.get("name", "")}}
                for a in kwargs.get("attendees", [])
            ]
        }

    def delete_event(self, *args, **kwargs) -> bool:
        return True 