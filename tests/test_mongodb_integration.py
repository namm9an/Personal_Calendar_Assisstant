import pytest
import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from src.db.connection import mongodb, settings
from src.models.mongodb_models import User, Event, Session, AgentLog
from src.repositories.mongodb_repository import MongoDBRepository
from src.core.exceptions import DatabaseError, NotFoundError

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create a test database connection."""
    # Use a test database
    test_db_name = f"{settings.MONGODB_DB_NAME}_test"
    client = AsyncIOMotorClient(settings.MONGODB_URI)
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
async def repository(test_db):
    """Create a repository instance with test database."""
    mongodb.db = test_db
    return MongoDBRepository()

@pytest.fixture
async def test_user(repository):
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        timezone="UTC",
        working_hours_start="09:00",
        working_hours_end="17:00"
    )
    return await repository.create_user(user)

@pytest.mark.asyncio
async def test_create_user(repository):
    """Test user creation."""
    user = User(
        email="new@example.com",
        name="New User",
        timezone="UTC"
    )
    created_user = await repository.create_user(user)
    assert created_user.email == user.email
    assert created_user.name == user.name
    assert created_user.timezone == user.timezone

@pytest.mark.asyncio
async def test_get_user_by_email(repository, test_user):
    """Test getting user by email."""
    user = await repository.get_user_by_email(test_user.email)
    assert user is not None
    assert user.email == test_user.email
    assert user.name == test_user.name

@pytest.mark.asyncio
async def test_create_event(repository, test_user):
    """Test event creation."""
    event = Event(
        user_id=str(test_user.id),
        summary="Test Event",
        start=datetime.utcnow(),
        end=datetime.utcnow() + timedelta(hours=1),
        provider="google"
    )
    created_event = await repository.create_event(event)
    assert created_event.summary == event.summary
    assert created_event.user_id == str(test_user.id)

@pytest.mark.asyncio
async def test_get_user_events(repository, test_user):
    """Test getting user events."""
    # Create test events
    now = datetime.utcnow()
    events = [
        Event(
            user_id=str(test_user.id),
            summary=f"Event {i}",
            start=now + timedelta(hours=i),
            end=now + timedelta(hours=i+1),
            provider="google"
        )
        for i in range(3)
    ]
    
    for event in events:
        await repository.create_event(event)
    
    # Get events
    user_events = await repository.get_user_events(
        test_user.id,
        now,
        now + timedelta(hours=4)
    )
    assert len(user_events) == 3

@pytest.mark.asyncio
async def test_create_session(repository, test_user):
    """Test session creation."""
    session = Session(
        user_id=str(test_user.id),
        token="test_token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        provider="google"
    )
    created_session = await repository.create_session(session)
    assert created_session.token == session.token
    assert created_session.user_id == str(test_user.id)

@pytest.mark.asyncio
async def test_get_active_session(repository, test_user):
    """Test getting active session."""
    # Create active session
    session = Session(
        user_id=str(test_user.id),
        token="test_token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        provider="google"
    )
    await repository.create_session(session)
    
    # Get active session
    active_session = await repository.get_active_session(test_user.id, "google")
    assert active_session is not None
    assert active_session.token == session.token

@pytest.mark.asyncio
async def test_create_agent_log(repository, test_user):
    """Test agent log creation."""
    log = AgentLog(
        user_id=str(test_user.id),
        action="test_action",
        input_text="test input",
        output_text="test output",
        status="success"
    )
    created_log = await repository.create_agent_log(log)
    assert created_log.action == log.action
    assert created_log.input_text == log.input_text

@pytest.mark.asyncio
async def test_get_user_agent_logs(repository, test_user):
    """Test getting user agent logs."""
    # Create test logs
    logs = [
        AgentLog(
            user_id=str(test_user.id),
            action=f"action_{i}",
            input_text=f"input_{i}",
            output_text=f"output_{i}",
            status="success"
        )
        for i in range(3)
    ]
    
    for log in logs:
        await repository.create_agent_log(log)
    
    # Get logs
    user_logs = await repository.get_user_agent_logs(test_user.id)
    assert len(user_logs) == 3

@pytest.mark.asyncio
async def test_error_handling(repository):
    """Test error handling."""
    # Test not found error
    with pytest.raises(NotFoundError):
        await repository.get_user_by_email("nonexistent@example.com")
    
    # Test database error with invalid data
    with pytest.raises(DatabaseError):
        await repository.create_user(User(
            email="invalid_email",  # Invalid email format
            timezone="UTC"
        )) 