"""
Smoke test for calendar tools.

Run this script with: python -m tests.smoke_test
"""
import logging
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_smoke_test():
    """Run a basic smoke test for calendar tools."""
    logger.info("Starting smoke test...")
    
    try:
        # Import dependencies here to avoid import errors
        from app.db.postgres import get_db
        from app.agent.tools import (
            list_events_tool,
            create_event_tool,
            update_event_tool,
            delete_event_tool,
            reschedule_event_tool,
        )
        from app.core.exceptions import ToolExecutionError
        from app.schemas.tool_schemas import (
            ListEventsInput,
            CreateEventInput,
            UpdateEventInput,
            DeleteEventInput,
            RescheduleEventInput,
            EventSchema,
            AttendeeSchema,
        )
        
        # Get database session
        db = next(get_db())
        
        try:
            # Test list_events with mocked GoogleCalendarService
            logger.info("Testing list_events with mocked GoogleCalendarService...")

            base_list_time = datetime.now(timezone.utc)
            start_time_for_list = base_list_time.replace(hour=9, minute=0, second=0, microsecond=0)
            end_time_for_list = base_list_time.replace(hour=17, minute=0, second=0, microsecond=0)

            list_google_event_input_args = {
                "provider": "google",
                "user_id": "test_user_id",
                "start": start_time_for_list,
                "end": end_time_for_list
            }

            with patch('app.agent.tools.GoogleCalendarService') as MockGoogleCalendarService:
                mock_google_service = MagicMock()
                mock_google_service.list_events.return_value = [
                    {
                        "id": "mock_google_event_1",
                        "summary": "Mock Google Event",
                        "start": {"dateTime": start_time_for_list.isoformat(), "timeZone": "UTC"},
                        "end": {"dateTime": (start_time_for_list + timedelta(hours=1)).isoformat(), "timeZone": "UTC"},
                        "attendees": [{"email": "test@example.com"}],
                        "htmlLink": "https://calendar.google.com/event?id=123"
                    }
                ]
                MockGoogleCalendarService.return_value = mock_google_service

                google_list_result = list_events_tool(ListEventsInput(**list_google_event_input_args))
                google_list_result_str = json.dumps(google_list_result.model_dump(), indent=2)

                expected_google_list_result_dict = {
                    "events": [
                        {
                            "id": "mock_google_event_1",
                            "summary": "Mock Google Event",
                            "start": start_time_for_list.isoformat(),
                            "end": (start_time_for_list + timedelta(hours=1)).isoformat(),
                            "description": None,
                            "location": None,
                            "attendees": [{"email": "test@example.com", "name": None}],
                            "html_link": "https://calendar.google.com/event?id=123"
                        }
                    ]
                }

                assert json.loads(google_list_result_str) == expected_google_list_result_dict, \
                    f"Mocked Google list_events output did not match expected.\nGot: {google_list_result_str}\nExpected: {json.dumps(expected_google_list_result_dict, indent=2)}"
                
                logger.info("Mocked Google list_events data processing test completed successfully")

            # Test list_events with mocked MicrosoftCalendarService
            logger.info("Testing list_events with mocked MicrosoftCalendarService...")

            list_ms_event_input_args = {
                "provider": "microsoft",
                "user_id": "test_user_id",
                "start": start_time_for_list,
                "end": end_time_for_list
            }

            with patch('app.agent.tools.MicrosoftCalendarService') as MockMicrosoftCalendarService:
                mock_ms_service = MagicMock()
                mock_ms_service.list_events.return_value = [
                    {
                        "id": "mock_ms_event_1",
                        "subject": "Mock MS Event",
                        "start": {"dateTime": start_time_for_list.isoformat(), "timeZone": "UTC"},
                        "end": {"dateTime": (start_time_for_list + timedelta(hours=1)).isoformat(), "timeZone": "UTC"},
                        "attendees": [{"emailAddress": {"address": "test@example.com"}}],
                        "webLink": "https://outlook.office.com/calendar/item/123"
                    }
                ]
                MockMicrosoftCalendarService.return_value = mock_ms_service

                ms_list_result = list_events_tool(ListEventsInput(**list_ms_event_input_args))
                ms_list_result_str = json.dumps(ms_list_result.model_dump(), indent=2)

                expected_ms_list_result_dict = {
                    "events": [
                        {
                            "id": "mock_ms_event_1",
                            "summary": "Mock MS Event",
                            "start": start_time_for_list.isoformat(),
                            "end": (start_time_for_list + timedelta(hours=1)).isoformat(),
                            "description": None,
                            "location": None,
                            "attendees": [{"email": "test@example.com", "name": None}],
                            "html_link": "https://outlook.office.com/calendar/item/123"
                        }
                    ]
                }

                assert json.loads(ms_list_result_str) == expected_ms_list_result_dict, \
                    f"Mocked MS list_events output did not match expected.\nGot: {ms_list_result_str}\nExpected: {json.dumps(expected_ms_list_result_dict, indent=2)}"
                
                logger.info("Mocked Microsoft list_events data processing test completed successfully")

            # Test create_event with mocked GoogleCalendarService
            logger.info("Testing create_event with mocked GoogleCalendarService...")

            base_create_time = datetime.now(timezone.utc) + timedelta(days=10)
            start_time_for_create = base_create_time.replace(hour=14, minute=0, second=0, microsecond=0)
            end_time_for_create = base_create_time.replace(hour=15, minute=0, second=0, microsecond=0)

            create_google_event_input_args = {
                "provider": "google",
                "user_id": "test_user_id",
                "summary": "Google Project Sync",
                "start": start_time_for_create,
                "end": end_time_for_create,
                "attendees": [
                    AttendeeSchema(email="google_dev@example.com"),
                    AttendeeSchema(email="google_lead@example.com", name="Google Team Lead")
                ],
                "description": "Sync up on Google project deliverables.",
                "location": "Google Meet"
            }

            with patch('app.agent.tools.GoogleCalendarService') as MockGoogleCalendarService:
                mock_google_service = MagicMock()
                mock_google_service.create_event.return_value = {
                    "id": "mock_google_event_2",
                    "summary": create_google_event_input_args["summary"],
                    "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "UTC"},
                    "description": create_google_event_input_args["description"],
                    "location": create_google_event_input_args["location"],
                    "attendees": [
                        {"email": "google_dev@example.com"},
                        {"email": "google_lead@example.com", "displayName": "Google Team Lead"}
                    ],
                    "htmlLink": "https://calendar.google.com/event?id=456"
                }
                MockGoogleCalendarService.return_value = mock_google_service

                google_create_result = create_event_tool(CreateEventInput(**create_google_event_input_args))
                google_create_result_str = json.dumps(google_create_result.model_dump(), indent=2)

                expected_google_create_result_dict = {
                    "id": "mock_google_event_2",
                    "summary": "Google Project Sync",
                    "start": start_time_for_create.isoformat(),
                    "end": end_time_for_create.isoformat(),
                    "description": "Sync up on Google project deliverables.",
                    "location": "Google Meet",
                    "attendees": [
                        {"email": "google_dev@example.com", "name": None},
                        {"email": "google_lead@example.com", "name": "Google Team Lead"}
                    ],
                    "html_link": "https://calendar.google.com/event?id=456"
                }

                assert json.loads(google_create_result_str) == expected_google_create_result_dict, \
                    f"Mocked Google create_event output did not match expected.\nGot: {google_create_result_str}\nExpected: {json.dumps(expected_google_create_result_dict, indent=2)}"
                
                logger.info("Mocked Google create_event data processing test completed successfully")

            # Test create_event with mocked MicrosoftCalendarService
            logger.info("Testing create_event with mocked MicrosoftCalendarService...")

            create_ms_event_input_args = {
                "provider": "microsoft",
                "user_id": "test_user_id",
                "summary": "MS Project Sync",
                "start": start_time_for_create,
                "end": end_time_for_create,
                "attendees": [
                    AttendeeSchema(email="ms_dev@example.com"),
                    AttendeeSchema(email="ms_lead@example.com", name="MS Team Lead")
                ],
                "description": "Sync up on Microsoft project deliverables.",
                "location": "Teams Meeting"
            }

            with patch('app.agent.tools.MicrosoftCalendarService') as MockMicrosoftCalendarService:
                mock_ms_service = MagicMock()
                mock_ms_service.create_event.return_value = {
                    "id": "mock_ms_event_2",
                    "subject": create_ms_event_input_args["summary"],
                    "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "UTC"},
                    "body": {"content": create_ms_event_input_args["description"]},
                    "location": {"displayName": create_ms_event_input_args["location"]},
                "attendees": [
                    {"emailAddress": {"address": "ms_dev@example.com"}},
                    {"emailAddress": {"address": "ms_lead@example.com", "name": "MS Team Lead"}}
                ],
                    "webLink": "https://outlook.office.com/calendar/item/789"
                }
                MockMicrosoftCalendarService.return_value = mock_ms_service

                ms_create_result = create_event_tool(CreateEventInput(**create_ms_event_input_args))
                ms_create_result_str = json.dumps(ms_create_result.model_dump(), indent=2)

                expected_ms_create_result_dict = {
                    "id": "mock_ms_event_2",
                    "summary": "MS Project Sync",
                    "start": start_time_for_create.isoformat(),
                    "end": end_time_for_create.isoformat(),
                    "description": "Sync up on Microsoft project deliverables.",
                    "location": "Teams Meeting",
                    "attendees": [
                        {"email": "ms_dev@example.com", "name": None},
                        {"email": "ms_lead@example.com", "name": "MS Team Lead"}
                    ],
                    "html_link": "https://outlook.office.com/calendar/item/789"
                }

                assert json.loads(ms_create_result_str) == expected_ms_create_result_dict, \
                    f"Mocked MS create_event output did not match expected.\nGot: {ms_create_result_str}\nExpected: {json.dumps(expected_ms_create_result_dict, indent=2)}"
                
                logger.info("Mocked Microsoft create_event data processing test completed successfully")

            # Test update_event with mocked GoogleCalendarService
            logger.info("Testing update_event with mocked GoogleCalendarService...")

            update_google_event_input_args = {
                "provider": "google",
                "user_id": "test_user_id",
                "event_id": "mock_google_event_1",
                "summary": "Updated Google Event",
                "start": start_time_for_create,
                "end": end_time_for_create,
                "description": "Updated Google event description",
                "location": "Updated Google Meet"
            }

            with patch('app.agent.tools.GoogleCalendarService') as MockGoogleCalendarService:
                mock_google_service = MagicMock()
                mock_google_service.update_event.return_value = {
                    "id": "mock_google_event_1",
                    "summary": update_google_event_input_args["summary"],
                    "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "UTC"},
                    "description": update_google_event_input_args["description"],
                    "location": update_google_event_input_args["location"],
                    "htmlLink": "https://calendar.google.com/event?id=789"
                }
                MockGoogleCalendarService.return_value = mock_google_service

                google_update_result = update_event_tool(UpdateEventInput(**update_google_event_input_args))
                google_update_result_str = json.dumps(google_update_result.model_dump(), indent=2)

                expected_google_update_result_dict = {
                    "id": "mock_google_event_1",
                    "summary": "Updated Google Event",
                    "start": start_time_for_create.isoformat(),
                    "end": end_time_for_create.isoformat(),
                    "description": "Updated Google event description",
                    "location": "Updated Google Meet",
                    "attendees": [],
                    "html_link": "https://calendar.google.com/event?id=789"
                }

                assert json.loads(google_update_result_str) == expected_google_update_result_dict, \
                    f"Mocked Google update_event output did not match expected.\nGot: {google_update_result_str}\nExpected: {json.dumps(expected_google_update_result_dict, indent=2)}"
                
                logger.info("Mocked Google update_event data processing test completed successfully")

            # Test update_event with mocked MicrosoftCalendarService
            logger.info("Testing update_event with mocked MicrosoftCalendarService...")

            update_ms_event_input_args = {
                "provider": "microsoft",
                "user_id": "test_user_id",
                "event_id": "mock_ms_event_1",
                "summary": "Updated MS Event",
                "start": start_time_for_create,
                "end": end_time_for_create,
                "description": "Updated MS event description",
                "location": "Updated MS Teams Meeting"
            }

            with patch('app.agent.tools.MicrosoftCalendarService') as MockMicrosoftCalendarService:
                mock_ms_service = MagicMock()
                mock_ms_service.update_event.return_value = {
                    "id": "mock_ms_event_1",
                    "subject": update_ms_event_input_args["summary"],
                    "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "UTC"},
                    "body": {"content": update_ms_event_input_args["description"]},
                    "location": {"displayName": update_ms_event_input_args["location"]},
                    "webLink": "https://outlook.office.com/calendar/item/789"
                }
                MockMicrosoftCalendarService.return_value = mock_ms_service

                ms_update_result = update_event_tool(UpdateEventInput(**update_ms_event_input_args))
                ms_update_result_str = json.dumps(ms_update_result.model_dump(), indent=2)

                expected_ms_update_result_dict = {
                    "id": "mock_ms_event_1",
                    "summary": "Updated MS Event",
                    "start": start_time_for_create.isoformat(),
                    "end": end_time_for_create.isoformat(),
                    "description": "Updated MS event description",
                    "location": "Updated MS Teams Meeting",
                    "attendees": [],
                    "html_link": "https://outlook.office.com/calendar/item/789"
                }

                assert json.loads(ms_update_result_str) == expected_ms_update_result_dict, \
                    f"Mocked MS update_event output did not match expected.\nGot: {ms_update_result_str}\nExpected: {json.dumps(expected_ms_update_result_dict, indent=2)}"
                
                logger.info("Mocked Microsoft update_event data processing test completed successfully")

            # Test delete_event with mocked GoogleCalendarService
            logger.info("Testing delete_event with mocked GoogleCalendarService...")

            delete_google_event_input_args = {
                "provider": "google",
                "user_id": "test_user_id",
                "event_id": "mock_google_event_1"
            }

            with patch('app.agent.tools.GoogleCalendarService') as MockGoogleCalendarService:
                mock_google_service = MagicMock()
                mock_google_service.delete_event.return_value = True
                MockGoogleCalendarService.return_value = mock_google_service

                google_delete_result = delete_event_tool(DeleteEventInput(**delete_google_event_input_args))
                assert google_delete_result is True
                logger.info("Mocked Google delete_event test completed successfully")

            # Test delete_event with mocked MicrosoftCalendarService
            logger.info("Testing delete_event with mocked MicrosoftCalendarService...")

            delete_ms_event_input_args = {
                "provider": "microsoft",
                "user_id": "test_user_id",
                "event_id": "mock_ms_event_1"
            }

            with patch('app.agent.tools.MicrosoftCalendarService') as MockMicrosoftCalendarService:
                mock_ms_service = MagicMock()
                mock_ms_service.delete_event.return_value = True
                MockMicrosoftCalendarService.return_value = mock_ms_service

                ms_delete_result = delete_event_tool(DeleteEventInput(**delete_ms_event_input_args))
                assert ms_delete_result is True
                logger.info("Mocked Microsoft delete_event test completed successfully")

            # Test reschedule_event with mocked GoogleCalendarService
            logger.info("Testing reschedule_event with mocked GoogleCalendarService...")

            reschedule_google_event_input_args = {
                "provider": "google",
                "user_id": "test_user_id",
                "event_id": "mock_google_event_1",
                "new_start": start_time_for_create,
                "new_end": end_time_for_create
            }

            with patch('app.agent.tools.GoogleCalendarService') as MockGoogleCalendarService:
                mock_google_service = MagicMock()
                mock_google_service.update_event.return_value = {
                    "id": "mock_google_event_1",
                    "summary": "Rescheduled Google Event",
                    "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "UTC"},
                    "htmlLink": "https://calendar.google.com/event?id=123"
                }
                MockGoogleCalendarService.return_value = mock_google_service

                google_reschedule_result = reschedule_event_tool(RescheduleEventInput(**reschedule_google_event_input_args))
                google_reschedule_result_str = json.dumps(google_reschedule_result.model_dump(), indent=2)

                expected_google_reschedule_result_dict = {
                    "id": "mock_google_event_1",
                    "summary": "Rescheduled Google Event",
                    "start": start_time_for_create.isoformat(),
                    "end": end_time_for_create.isoformat(),
                    "description": None,
                    "location": None,
                    "attendees": [],
                    "html_link": "https://calendar.google.com/event?id=123"
                }

                assert json.loads(google_reschedule_result_str) == expected_google_reschedule_result_dict, \
                    f"Mocked Google reschedule_event output did not match expected.\nGot: {google_reschedule_result_str}\nExpected: {json.dumps(expected_google_reschedule_result_dict, indent=2)}"
                
                logger.info("Mocked Google reschedule_event data processing test completed successfully")

            # Test reschedule_event with mocked MicrosoftCalendarService
            logger.info("Testing reschedule_event with mocked MicrosoftCalendarService...")

            reschedule_ms_event_input_args = {
                "provider": "microsoft",
                "user_id": "test_user_id",
                "event_id": "mock_ms_event_1",
                "new_start": start_time_for_create,
                "new_end": end_time_for_create
            }

            with patch('app.agent.tools.MicrosoftCalendarService') as MockMicrosoftCalendarService:
                mock_ms_service = MagicMock()
                mock_ms_service.update_event.return_value = {
                    "id": "mock_ms_event_1",
                    "subject": "Rescheduled MS Event",
                    "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "UTC"},
                    "webLink": "https://outlook.office.com/calendar/item/123"
                }
                MockMicrosoftCalendarService.return_value = mock_ms_service

                ms_reschedule_result = reschedule_event_tool(RescheduleEventInput(**reschedule_ms_event_input_args))
                ms_reschedule_result_str = json.dumps(ms_reschedule_result.model_dump(), indent=2)

                expected_ms_reschedule_result_dict = {
                    "id": "mock_ms_event_1",
                    "summary": "Rescheduled MS Event",
                    "start": start_time_for_create.isoformat(),
                    "end": end_time_for_create.isoformat(),
                    "description": None,
                    "location": None,
                    "attendees": [],
                    "html_link": "https://outlook.office.com/calendar/item/123"
                }

                assert json.loads(ms_reschedule_result_str) == expected_ms_reschedule_result_dict, \
                    f"Mocked MS reschedule_event output did not match expected.\nGot: {ms_reschedule_result_str}\nExpected: {json.dumps(expected_ms_reschedule_result_dict, indent=2)}"
                
                logger.info("Mocked Microsoft reschedule_event data processing test completed successfully")

            logger.info("All smoke tests completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Error during smoke test: {str(e)}")
            return False
            
    except ImportError as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
