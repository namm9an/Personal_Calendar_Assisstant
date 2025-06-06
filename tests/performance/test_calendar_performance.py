"""
Performance tests for calendar operations.
"""
import time
import psutil
import pytest
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from app.agent.tools import CalendarTools, ListEventsInput, CreateEventInput
from app.models.user import User
from app.models.mongodb_models import Event, Session
from motor.motor_asyncio import AsyncIOMotorClient

def measure_response_time(func, *args, **kwargs):
    """Measure the response time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def get_memory_usage():
    """Get current memory usage of the process."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

def get_cpu_usage():
    """Get current CPU usage of the process."""
    process = psutil.Process()
    return process.cpu_percent()

@pytest.fixture
async def mongodb_client():
    """Create a MongoDB client for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    await client.drop_database("test_calendar_db")

@pytest.fixture
async def test_db(mongodb_client):
    """Get the test database."""
    db = mongodb_client["test_calendar_db"]
    yield db
    await db.client.drop_database("test_calendar_db")

@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        email="test@example.com",
        name="Test User",
        timezone="UTC",
        working_hours_start="09:00",
        working_hours_end="17:00"
    )

@pytest.fixture
async def db_session(test_db):
    """Create a test database session."""
    return test_db

@pytest.fixture
def calendar_tools(test_user, db_session):
    """Create calendar tools instance."""
    return CalendarTools(user=test_user, db=db_session, provider="google")

class TestCalendarPerformance:
    """Performance tests for calendar operations."""

    def test_list_events_response_time(self, calendar_tools):
        """Test response time for listing events."""
        start_time = time.time()
        
        # List events for the next 7 days
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        result = calendar_tools.list_events({
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": end_date,
            "max_results": 10
        })
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 1.0  # Should complete within 1 second
        assert isinstance(result, str)  # Should return a string result

    def test_create_event_response_time(self, calendar_tools):
        """Test response time for creating an event."""
        start_time = time.time()
        
        # Create a test event
        event_data = {
            "summary": "Performance Test Event",
            "start_datetime": (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "duration_minutes": 30,
            "description": "Test event for performance testing"
        }
        result = calendar_tools.create_event(event_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 2.0  # Should complete within 2 seconds
        assert isinstance(result, str)  # Should return a string result

    def test_concurrent_requests(self, calendar_tools):
        """Test handling of concurrent requests."""
        async def make_request():
            return calendar_tools.list_events({
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "max_results": 5
            })
        
        # Create 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        
        assert len(results) == 10
        assert all(isinstance(result, str) for result in results)

    def test_resource_usage(self, calendar_tools):
        """Test resource usage during calendar operations."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_cpu = process.cpu_percent()
        
        # Perform a series of operations
        for _ in range(5):
            calendar_tools.list_events({
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "max_results": 5
            })
        
        final_memory = process.memory_info().rss
        final_cpu = process.cpu_percent()
        
        # Check memory usage (should not increase by more than 50MB)
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # Convert to MB
        assert memory_increase < 50
        
        # Check CPU usage (should not exceed 80%)
        assert final_cpu < 80

    def test_bulk_operations(self, calendar_tools):
        """Test performance of bulk operations."""
        start_time = time.time()
        
        # Create 5 events in sequence
        for i in range(5):
            event_data = {
                "summary": f"Bulk Test Event {i+1}",
                "start_datetime": (datetime.now() + timedelta(hours=i+1)).strftime("%Y-%m-%d %H:%M"),
                "duration_minutes": 30
            }
            calendar_tools.create_event(event_data)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert total_time < 10.0  # Should complete within 10 seconds 