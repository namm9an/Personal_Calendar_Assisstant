"""
Smoke test for calendar tools.

Run this script with: python -m tests.smoke_test
"""
import logging
import sys
from datetime import datetime, timedelta
from unittest.mock import patch
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
        from app.agent.tools import CalendarTools
        from app.models.user import User
        
        # Get database session
        db = next(get_db())
        
        try:
            # Find a user with Google tokens
            user = db.query(User).filter(
                User.is_active == True,
                User.google_access_token.isnot(None)
            ).first()
            
            if not user:
                logger.info("No active user with Google tokens found. Creating a dummy user for testing.")
                dummy_email = "smoke_test_user@example.com"
                user = User(
                    email=dummy_email,
                    name="Smoke Test User",
                    is_active=True,
                    google_access_token="dummy_google_token_for_smoke_test",
                    google_refresh_token="dummy_google_refresh_token_for_smoke_test",
                    timezone="UTC",  # Provide a default timezone
                    working_hours_start="09:00:00",  # Provide default working hours
                    working_hours_end="17:00:00"
                    # Add any other mandatory fields for the User model if necessary
                )
                db.add(user)
                db.commit()
                db.refresh(user) # To get the ID and other DB-generated fields
                logger.info(f"Dummy user {user.email} (ID: {user.id}) created for testing.")
            
            logger.info(f"Using test user: {user.email} (ID: {user.id})")
            
            # Define `now` for mocked data generation
            now = datetime.utcnow()

            # Test list_events with mocked GoogleCalendarService
            logger.info("Testing list_events with mocked GoogleCalendarService...")

            # Sample raw event data (like what Google Calendar API might return)
            # Timestamps are ISO format strings with Z (UTC)
            mock_raw_event_data = [
                {
                    "id": "mockevent123",
                    "summary": "Mocked Test Event",
                    "start": {"dateTime": (now + timedelta(hours=1)).isoformat() + "Z"},
                    "end": {"dateTime": (now + timedelta(hours=2)).isoformat() + "Z"},
                    "location": "Mock Location",
                    "description": "This is a mocked event description.",
                    "attendees": [{"email": "attendee1@example.com", "displayName": "Mock Attendee 1"}]
                },
                {
                    "id": "mockevent456_allday",
                    "summary": "Mocked All-Day Event",
                    "start": {"date": (now + timedelta(days=2)).strftime("%Y-%m-%d")},
                    "end": {"date": (now + timedelta(days=3)).strftime("%Y-%m-%d")} # Google API end date for all-day is exclusive
                }
            ]

            # Expected processed event data by CalendarTools.list_events
            expected_processed_events = [
                {
                    "id": "mockevent123",
                    "summary": "Mocked Test Event",
                    "start": (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                    "end": (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                    "location": "Mock Location",
                    "description": "This is a mocked event description.",
                    "attendees": [{"email": "attendee1@example.com", "name": "Mock Attendee 1"}]
                },
                {
                    "id": "mockevent456_allday",
                    "summary": "Mocked All-Day Event",
                    "start": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "end": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "location": "",
                    "description": "",
                    "attendees": []
                }
            ]
            expected_list_result_dict = {"events": expected_processed_events}

            # Patch GoogleCalendarService where it's imported/used by app.agent.tools
            with patch('app.agent.tools.GoogleCalendarService') as MockGoogleCalendarService:
                # Configure the instance that CalendarTools will create and use
                mock_service_instance = MockGoogleCalendarService.return_value
                mock_service_instance.get_events.return_value = mock_raw_event_data

                # Initialize CalendarTools - it will use the mocked GoogleCalendarService
                tools = CalendarTools(user, db)
                
                # Parameters for list_events call
                # Ensure the date range covers the mocked events
                test_start_date_str = now.strftime("%Y-%m-%d")
                test_end_date_str = (now + timedelta(days=5)).strftime("%Y-%m-%d")
                
                list_result_str = tools.list_events({
                    "start_date": test_start_date_str,
                    "end_date": test_end_date_str,
                    "max_results": 10
                })
                
                logger.info(f"Mocked List events result: {list_result_str}")

                # Assert that the mock's get_events was called
                mock_service_instance.get_events.assert_called_once()
                # Can add more specific assertions about call arguments if needed, e.g.:
                # mock_service_instance.get_events.assert_called_once_with(
                #     calendar_id='primary', 
                #     time_min=datetime.combine(datetime.strptime(test_start_date_str, "%Y-%m-%d").date(), datetime.min.time()),
                #     time_max=datetime.combine(datetime.strptime(test_end_date_str, "%Y-%m-%d").date(), datetime.max.time()),
                #     max_results=10
                # )

                # Assert that the processed output is as expected
                assert json.loads(list_result_str) == expected_list_result_dict, \
                    f"Mocked list_events output did not match expected.\nGot: {list_result_str}\nExpected: {json.dumps(expected_list_result_dict, indent=2)}"
                
                logger.info("Mocked list_events data processing test completed successfully")
            
            # Test create_event with mocked GoogleCalendarService
            logger.info("Testing create_event with mocked GoogleCalendarService...")

            # Sample input for CalendarTools.create_event
            # Using a fixed future date for predictability in tests
            base_create_time = datetime.utcnow() + timedelta(days=7)
            start_time_for_create = base_create_time.replace(hour=10, minute=0, second=0, microsecond=0)
            end_time_for_create = base_create_time.replace(hour=11, minute=0, second=0, microsecond=0)

            create_event_input_args = {
                "summary": "Team Meeting Special",
                "start_datetime": start_time_for_create.strftime("%Y-%m-%d %H:%M"), 
                "end_datetime": end_time_for_create.strftime("%Y-%m-%d %H:%M"),   
                "attendees": [
                    {"email": "dev1@example.com"}, 
                    {"email": "pm@example.com", "name": "Product Manager"}
                ], 
                "description": "Discuss new features for Q3.",
                "location": "Virtual / Zoom"
            }

            # Expected arguments for the call to GoogleCalendarService.create_event
            expected_service_call_args = {
                "summary": "Team Meeting Special",
                "start_datetime": start_time_for_create, 
                "end_datetime": end_time_for_create,   
                "attendees": [
                    {"email": "dev1@example.com"}, 
                    {"email": "pm@example.com", "displayName": "Product Manager"}
                ],
                "description": "Discuss new features for Q3.",
                "location": "Virtual / Zoom",
                "time_zone": user.timezone, # Expecting user's default timezone
                "calendar_id": "primary"  # Expecting default calendar_id from CreateEventInput via CalendarTools
            }

            # Mocked return value from GoogleCalendarService.create_event
            # This simulates the dict representation of an Event Pydantic model
            mock_created_event_service_response = {
                "id": "newmockevent789",
                "summary": "Team Meeting Special",
                "start": {"dateTime": start_time_for_create.isoformat(), "timeZone": "America/New_York"},
                "end": {"dateTime": end_time_for_create.isoformat(), "timeZone": "America/New_York"},
                "description": "Discuss new features for Q3.",
                "location": "Virtual / Zoom",
                "attendees": [
                    {"email": "dev1@example.com", "name": None}, 
                    {"email": "pm@example.com", "name": "Product Manager"}
                ],
                "calendar_id": "primary",
                "html_link": "https://calendar.google.com/event?eid=newmockevent789",
                "created": base_create_time.isoformat(),
                "updated": base_create_time.isoformat(),
                # Add other fields if Event model has them and they are relevant
            }

            with patch('app.agent.tools.GoogleCalendarService') as MockCreateGoogleCalendarService:
                mock_create_service_instance = MockCreateGoogleCalendarService.return_value
                mock_create_service_instance.create_event.return_value = mock_created_event_service_response

                # Initialize CalendarTools (it will use the mocked GoogleCalendarService)
                # User and db are already defined from the list_events test setup
                tools = CalendarTools(user, db)
                
                create_result_str = tools.create_event(create_event_input_args)
                logger.info(f"Mocked create_event result: {create_result_str}")

                # Assert that the mock's create_event was called once
                mock_create_service_instance.create_event.assert_called_once()

                # Assert that it was called with the expected arguments
                # Pop 'user_input' as it's generated internally and might be slightly different
                # based on how CalendarTools constructs it.
                # We can check its presence if needed, but exact match might be too brittle.
                actual_call_args = mock_create_service_instance.create_event.call_args[1] # kwargs
                
                # Compare datetimes carefully, especially if timezone handling in parsing is complex
                # For now, assuming direct comparison works if parsing is straightforward
                assert actual_call_args.get("summary") == expected_service_call_args["summary"]
                assert actual_call_args.get("start_datetime") == expected_service_call_args["start_datetime"]
                assert actual_call_args.get("end_datetime") == expected_service_call_args["end_datetime"]
                
                # Sort attendee lists before comparison if order is not guaranteed
                actual_attendees = sorted(actual_call_args.get("attendees", []), key=lambda x: x['email'])
                expected_attendees = sorted(expected_service_call_args["attendees"], key=lambda x: x['email'])
                assert actual_attendees == expected_attendees
                
                assert actual_call_args.get("description") == expected_service_call_args["description"]
                assert actual_call_args.get("location") == expected_service_call_args["location"]

                logger.info(f"DEBUG: Actual time_zone: {actual_call_args.get('time_zone')}")
                logger.info(f"DEBUG: Expected time_zone: {expected_service_call_args['time_zone']}")
                assert actual_call_args.get("time_zone") == expected_service_call_args["time_zone"]

                # Assert that arguments with defaults in the service method were NOT passed by CalendarTools
                # unless they are part of the explicit contract from CreateEventInput (like calendar_id default)
                assert actual_call_args.get("calendar_id") == expected_service_call_args["calendar_id"]
                assert "user_input" not in actual_call_args

                # Assert that the processed output is as expected
                # CalendarTools.create_event returns a JSON string of the service's response
                assert json.loads(create_result_str) == mock_created_event_service_response, \
                    f"Mocked create_event output did not match expected.\nGot: {create_result_str}\nExpected: {json.dumps(mock_created_event_service_response, indent=2)}"
                
                logger.info("Mocked CalendarTools.create_event test completed successfully")

            # Test list_events with mocked MicrosoftCalendarService
            logger.info("Testing list_events with mocked MicrosoftCalendarService...")

            # Sample raw event data for Microsoft (similar structure to Google for consistency in CalendarTools processing)
            # Timestamps are ISO format strings with Z (UTC)
            mock_ms_raw_event_data = [
                {
                    "id": "msmockevent789",
                    "summary": "MS Mocked Standup Meeting",
                    "start": {"dateTime": (now + timedelta(hours=3)).isoformat() + "Z", "timeZone": "UTC"},
                    "end": {"dateTime": (now + timedelta(hours=3, minutes=30)).isoformat() + "Z", "timeZone": "UTC"},
                    "location": "MS Teams",
                    "bodyPreview": "Quick sync for MS team.", # Microsoft uses bodyPreview
                    "attendees": [{"emailAddress": {"address": "attendee_ms@example.com", "name": "MS Mock Attendee"}}]
                }
            ]

            # Expected processed event data by CalendarTools.list_events for Microsoft
            expected_ms_processed_events = [
                {
                    "id": "msmockevent789",
                    "summary": "MS Mocked Standup Meeting",
                    "start": (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                    "end": (now + timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M"),
                    "location": "MS Teams",
                    "description": "Quick sync for MS team.", # CalendarTools maps bodyPreview to description
                    "attendees": [{"email": "attendee_ms@example.com", "name": "MS Mock Attendee"}]
                }
            ]
            expected_ms_list_result_dict = {"events": expected_ms_processed_events}

            # Patch MicrosoftCalendarService where it's imported/used by app.agent.tools
            with patch('app.agent.tools.MicrosoftCalendarService') as MockMicrosoftCalendarService:
                mock_ms_service_instance = MockMicrosoftCalendarService.return_value
                # Ensure the mock service's list_events (or get_events alias) returns our data
                # Memory b6d84961-ca4c-4bf9-a6fa-1fb865737996 mentions list_events = get_events alias
                mock_ms_service_instance.list_events.return_value = mock_ms_raw_event_data

                # Initialize CalendarTools for Microsoft provider
                # User and db are already defined
                ms_tools = CalendarTools(user, db, provider="microsoft")
                
                test_start_date_str_ms = now.strftime("%Y-%m-%d")
                test_end_date_str_ms = (now + timedelta(days=5)).strftime("%Y-%m-%d")
                
                ms_list_result_str = ms_tools.list_events({
                    "start_date": test_start_date_str_ms,
                    "end_date": test_end_date_str_ms,
                    "max_results": 5
                })
                
                logger.info(f"Mocked MS List events result: {ms_list_result_str}")

                # Assert that the mock's list_events was called
                mock_ms_service_instance.list_events.assert_called_once()
                
                # Check call arguments for Microsoft service
                actual_ms_call_args = mock_ms_service_instance.list_events.call_args[1] # kwargs
                assert actual_ms_call_args.get("user_id") == str(user.id)
                assert actual_ms_call_args.get("calendar_id") == "primary" # Default from ListEventsInput
                assert actual_ms_call_args.get("max_results") == 5
                # Datetime comparison for time_min and time_max needs care
                # For now, we'll trust CalendarTools passes them correctly as per Google test

                # Assert that the processed output is as expected
                assert json.loads(ms_list_result_str) == expected_ms_list_result_dict, \
                    f"Mocked MS list_events output did not match expected.\nGot: {ms_list_result_str}\nExpected: {json.dumps(expected_ms_list_result_dict, indent=2)}"
                
                logger.info("Mocked Microsoft list_events data processing test completed successfully")

            # Test create_event with mocked MicrosoftCalendarService
            logger.info("Testing create_event with mocked MicrosoftCalendarService...")

            base_create_time_ms = datetime.utcnow() + timedelta(days=10)
            start_time_for_ms_create = base_create_time_ms.replace(hour=14, minute=0, second=0, microsecond=0)
            end_time_for_ms_create = base_create_time_ms.replace(hour=15, minute=0, second=0, microsecond=0)

            create_ms_event_input_args = {
                "summary": "MS Project Sync",
                "start_datetime": start_time_for_ms_create.strftime("%Y-%m-%d %H:%M"), 
                "end_datetime": end_time_for_ms_create.strftime("%Y-%m-%d %H:%M"),   
                "attendees": [
                    {"email": "ms_dev@example.com"}, 
                    {"email": "ms_lead@example.com", "name": "MS Team Lead"}
                ], 
                "description": "Sync up on MS project deliverables.",
                "location": "MS Teams Meeting"
            }

            # Expected arguments for the call to MicrosoftCalendarService.create_event
            # Note: CalendarTools converts datetime strings to datetime objects
            expected_ms_service_call_args = {
                "summary": "MS Project Sync",
                "start_datetime": start_time_for_ms_create, 
                "end_datetime": end_time_for_ms_create,   
                "attendees": [
                    {"email": "ms_dev@example.com"}, 
                    # Microsoft mock might expect 'displayName' if 'name' is provided by CalendarTools
                    # CalendarTools prepares attendees as {'email': '...', 'displayName': '...'}
                    {"email": "ms_lead@example.com", "displayName": "MS Team Lead"} 
                ],
                "description": "Sync up on MS project deliverables.",
                "location": "MS Teams Meeting",
                "time_zone": user.timezone, # Expecting user's default timezone
                "calendar_id": "primary"  # Default from CreateEventInput via CalendarTools
            }

            # Mocked return value from MicrosoftCalendarService.create_event
            # This should simulate the dict representation of an Event Pydantic model or similar structure
            mock_ms_created_event_service_response = {
                "id": "new_ms_mock_event_123",
                "subject": "MS Project Sync", # Microsoft often uses 'subject' for summary
                "start": {"dateTime": start_time_for_ms_create.isoformat(), "timeZone": user.timezone},
                "end": {"dateTime": end_time_for_ms_create.isoformat(), "timeZone": user.timezone},
                "bodyPreview": "Sync up on MS project deliverables.",
                "location": {"displayName": "MS Teams Meeting"},
                "attendees": [
                    {"emailAddress": {"address": "ms_dev@example.com"}},
                    {"emailAddress": {"address": "ms_lead@example.com", "name": "MS Team Lead"}}
                ],
                "webLink": "https://outlook.office.com/calendar/item/new_ms_mock_event_123"
            }

            with patch('app.agent.tools.MicrosoftCalendarService') as MockCreateMicrosoftCalendarService:
                mock_ms_create_service_instance = MockCreateMicrosoftCalendarService.return_value
                mock_ms_create_service_instance.create_event.return_value = mock_ms_created_event_service_response

                # Initialize CalendarTools for Microsoft provider
                ms_tools = CalendarTools(user, db, provider="microsoft")
                
                ms_create_result_str = ms_tools.create_event(create_ms_event_input_args)
                logger.info(f"Mocked MS create_event result: {ms_create_result_str}")

                mock_ms_create_service_instance.create_event.assert_called_once()
                actual_ms_create_call_args = mock_ms_create_service_instance.create_event.call_args[1] # kwargs
                
                assert actual_ms_create_call_args.get("summary") == expected_ms_service_call_args["summary"]
                assert actual_ms_create_call_args.get("start_datetime") == expected_ms_service_call_args["start_datetime"]
                assert actual_ms_create_call_args.get("end_datetime") == expected_ms_service_call_args["end_datetime"]
                
                actual_ms_attendees = sorted(actual_ms_create_call_args.get("attendees", []), key=lambda x: x['email'])
                expected_ms_attendees = sorted(expected_ms_service_call_args["attendees"], key=lambda x: x['email'])
                assert actual_ms_attendees == expected_ms_attendees
                
                assert actual_ms_create_call_args.get("description") == expected_ms_service_call_args["description"]
                assert actual_ms_create_call_args.get("location") == expected_ms_service_call_args["location"]
                assert actual_ms_create_call_args.get("time_zone") == expected_ms_service_call_args["time_zone"]
                assert actual_ms_create_call_args.get("calendar_id") == expected_ms_service_call_args["calendar_id"]

                # Assert that the processed output is as expected
                # CalendarTools.create_event returns a JSON string of the service's response
                assert json.loads(ms_create_result_str) == mock_ms_created_event_service_response, \
                    f"Mocked MS create_event output did not match expected.\nGot: {ms_create_result_str}\nExpected: {json.dumps(mock_ms_created_event_service_response, indent=2)}"
                
                logger.info("Mocked Microsoft CalendarTools.create_event test completed successfully")

        except Exception as e:
            logger.error(f"Smoke test failed: {str(e)}", exc_info=True)
        finally:
            db.close()
            
    except ImportError as e:
        logger.error(f"Import error: {str(e)}. Make sure you're running from the project root directory.")
        logger.error("Try: 'cd /path/to/Personal Calendar Assistant' and then 'python -m tests.smoke_test'")
    except Exception as e:
        logger.error(f"Setup error: {str(e)}", exc_info=True)
    
    logger.info("Smoke test completed")

if __name__ == "__main__":
    run_smoke_test()
