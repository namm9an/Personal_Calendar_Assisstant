import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from src.db.connection import mongodb, settings
from src.models.mongodb_models import User, Event, Session, AgentLog
from src.repositories.mongodb_repository import MongoRepository
from src.core.exceptions import DatabaseError, NotFoundError

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Create a test database connection."""
    # Use a test database
    test_db_name = "calendar_test_integration"
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[test_db_name]
    
    # Clear test database
    await db.users.delete_many({})
    await db.events.delete_many({})
    await db.sessions.delete_many({})
    await db.agent_logs.delete_many({})
    
    yield db
    
    # Cleanup after tests
    await client.drop_database(test_db_name)
    client.close()

@pytest.fixture
def repository(test_db):
    """Create a repository instance with test database."""
    mongodb.db = test_db
    repo = MongoRepository(test_db)
    return repo

@pytest_asyncio.fixture
async def initialized_repository(repository):
    """Create an initialized repository instance."""
    repo = await repository.initialize()
    return repo

@pytest_asyncio.fixture
async def test_user(initialized_repository):
    """Create a test user."""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "timezone": "UTC",
        "working_hours_start": "09:00",
        "working_hours_end": "17:00"
    }
    user = await initialized_repository.create_user(user_data)
    yield user
    # Cleanup
    await initialized_repository.users.delete_one({"email": "test@example.com"})

@pytest.mark.asyncio
async def test_create_user(initialized_repository):
    """Test user creation."""
    user_data = {
        "email": "new@example.com",
        "name": "New User",
        "timezone": "UTC"
    }
    created_user = await initialized_repository.create_user(user_data)
    assert created_user.email == user_data["email"]
    assert created_user.name == user_data["name"]
    assert created_user.timezone == user_data["timezone"]
    
    # Cleanup
    await initialized_repository.users.delete_one({"email": "new@example.com"})

@pytest.mark.asyncio
async def test_get_user_by_email(initialized_repository, test_user):
    """Test getting user by email."""
    user = await initialized_repository.get_user_by_email(test_user.email)
    assert user is not None
    assert user.email == test_user.email
    assert user.name == test_user.name

@pytest.mark.asyncio
async def test_create_event(initialized_repository, test_user):
    """Test event creation."""
    event_data = {
        "user_id": str(test_user.id),
        "summary": "Test Event",
        "start": datetime.utcnow(),
        "end": datetime.utcnow() + timedelta(hours=1),
        "provider": "google"
    }
    created_event = await initialized_repository.create_event(event_data)
    assert created_event.summary == event_data["summary"]
    assert created_event.user_id == str(test_user.id)

@pytest.mark.asyncio
async def test_get_user_events(initialized_repository, test_user):
    """Test getting user events."""
    # Create test events
    now = datetime.utcnow()
    for i in range(3):
        event_data = {
            "user_id": str(test_user.id),
            "summary": f"Event {i}",
            "start": now + timedelta(hours=i),
            "end": now + timedelta(hours=i+1),
            "provider": "google"
        }
        await initialized_repository.create_event(event_data)
    
    # Get events
    user_events = await initialized_repository.get_user_events(
        str(test_user.id),
        now,
        now + timedelta(hours=4)
    )
    assert len(user_events) >= 3

@pytest.mark.asyncio
async def test_create_session(initialized_repository, test_user):
    """Test session creation."""
    session_data = {
        "user_id": str(test_user.id),
        "token": "test_token",
        "expires_at": datetime.utcnow() + timedelta(hours=1),
        "provider": "google"
    }
    created_session = await initialized_repository.create_session(session_data)
    assert created_session.token == session_data["token"]
    assert created_session.user_id == str(test_user.id)

@pytest.mark.asyncio
async def test_get_active_session(initialized_repository, test_user):
    """Test getting active session."""
    # Create active session
    session_data = {
        "user_id": str(test_user.id),
        "token": "test_token",
        "expires_at": datetime.utcnow() + timedelta(hours=1),
        "provider": "google"
    }
    await initialized_repository.create_session(session_data)
    
    # Get active session
    active_session = await initialized_repository.get_active_session(str(test_user.id), "google")
    assert active_session is not None
    assert active_session.token == session_data["token"]

@pytest.mark.asyncio
async def test_create_agent_log(initialized_repository, test_user):
    """Test agent log creation."""
    log_data = {
        "user_id": str(test_user.id),
        "action": "test_action",
        "input_text": "test input",
        "output_text": "test output",
        "status": "success"
    }
    created_log = await initialized_repository.create_agent_log(log_data)
    assert created_log.action == log_data["action"]
    assert created_log.input_text == log_data["input_text"]

@pytest.mark.asyncio
async def test_get_user_agent_logs(initialized_repository, test_user):
    """Test getting user agent logs."""
    # Create test logs
    for i in range(3):
        log_data = {
            "user_id": str(test_user.id),
            "action": f"action_{i}",
            "input_text": f"input_{i}",
            "output_text": f"output_{i}",
            "status": "success"
        }
        await initialized_repository.create_agent_log(log_data)
    
    # Get logs
    user_logs = await initialized_repository.get_user_agent_logs(str(test_user.id))
    assert len(user_logs) >= 3

@pytest.mark.asyncio
async def test_error_handling(initialized_repository):
    """Test error handling."""
    # Test not found error
    with pytest.raises(NotFoundError):
        await initialized_repository.get_user_by_email("nonexistent@example.com")
    
    # Test database error with invalid data
    with pytest.raises(Exception):
        await initialized_repository.create_user({
            "email": "invalid_email",  # Invalid email format
            "timezone": "UTC"
        }) 