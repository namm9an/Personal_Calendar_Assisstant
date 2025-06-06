import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.agent_calendar import detect_intent, load_prompt_template
from src.schemas.agent_schemas import AgentRequest, AgentResponse, AgentStep, AgentError
from app.main import app
from app.config import settings
from app.core.exceptions import ToolExecutionError
from app.models.types import UniversalUUID
from app.models.mongodb_models import User, Event, Session
from datetime import datetime, timedelta
import json

client = TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "timezone": "UTC"
    }

@pytest.fixture
def test_session(test_user):
    """Create a test session."""
    return {
        "user_id": "test_user_id",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }

def test_detect_intent():
    """Test intent detection from user text."""
    # Test list events intent
    assert detect_intent("Show me my calendar for tomorrow") == "list_events"
    assert detect_intent("What events do I have today?") == "list_events"
    
    # Test find free slots intent
    assert detect_intent("Find a free slot tomorrow afternoon") == "find_free_slots"
    assert detect_intent("When am I available for a meeting?") == "find_free_slots"
    
    # Test create event intent
    assert detect_intent("Schedule a meeting with John tomorrow") == "create_event"
    assert detect_intent("Book a team meeting for Friday") == "create_event"
    
    # Test reschedule event intent
    assert detect_intent("Move my meeting to 3 PM") == "reschedule_event"
    assert detect_intent("Change the team meeting time") == "reschedule_event"
    
    # Test cancel event intent
    assert detect_intent("Cancel my meeting tomorrow") == "cancel_event"
    assert detect_intent("Delete the team meeting") == "cancel_event"
    
    # Test unknown intent
    assert detect_intent("Hello, how are you?") == "unknown"

def test_load_prompt_template():
    """Test loading and formatting prompt templates."""
    # Test loading list events template
    prompt = load_prompt_template("list_events", "Show me my calendar")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Show me my calendar" in prompt
    
    # Test loading find free slots template
    prompt = load_prompt_template("find_free_slots", "Find a free slot")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Find a free slot" in prompt
    
    # Test loading create event template
    prompt = load_prompt_template("create_event", "Schedule a meeting")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Schedule a meeting" in prompt
    
    # Test loading reschedule event template
    prompt = load_prompt_template("reschedule_event", "Move my meeting")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Move my meeting" in prompt
    
    # Test loading cancel event template
    prompt = load_prompt_template("cancel_event", "Cancel my meeting")
    assert "System: You are an AI scheduling assistant" in prompt
    assert "Cancel my meeting" in prompt
    
    # Test loading non-existent template
    with pytest.raises(Exception):
        load_prompt_template("unknown", "Some text")

@pytest.mark.asyncio
async def test_run_calendar_agent_success(client, mock_llm_selector, mock_langgraph_runner):
    """Test successful calendar agent execution."""
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_langgraph_runner.run_stream):
        
        response = client.post(
            "/api/v1/agent/calendar",
            json={
                "text": "Show me my calendar for tomorrow",
                "provider": "google"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # Parse SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:]  # Remove "data: " prefix
                events.append(event_data)
        
        # Should have 3 steps + final response
        assert len(events) == 4
        
        # First event should be a step
        step = AgentStep.parse_raw(events[0])
        assert step.step_number == 1
        assert "Analyzing" in step.message
        
        # Last event should be the final response
        final_response = AgentResponse.parse_raw(events[-1])
        assert final_response.final_intent == "list_events"
        assert final_response.summary.startswith("Successfully processed")

@pytest.mark.asyncio
async def test_run_calendar_agent_unknown_intent(client):
    """Test calendar agent with unknown intent."""
    response = client.post(
        "/api/v1/agent/calendar",
        json={
            "text": "Hello, how are you?",
            "provider": "google"
        }
    )
    
    assert response.status_code == 400
    error = AgentError.parse_raw(response.json())
    assert "Could not recognize intent" in error.error

@pytest.mark.asyncio
async def test_run_calendar_agent_llm_fallback(client, mock_llm_selector, mock_langgraph_runner):
    """Test calendar agent with LLM fallback."""
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_langgraph_runner.run_stream):
        
        response = client.post(
            "/api/v1/agent/calendar",
            json={
                "text": "Show me my calendar for tomorrow",
                "provider": "google"
            }
        )
        
        assert response.status_code == 200
        
        # Parse SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:]
                events.append(event_data)
        
        # Should still complete successfully despite fallback
        final_response = AgentResponse.parse_raw(events[-1])
        assert final_response.final_intent == "list_events"
        assert final_response.summary.startswith("Successfully processed")

@pytest.mark.asyncio
async def test_run_calendar_agent_tool_error(client, mock_llm_selector):
    """Test calendar agent with tool execution error."""
    # Mock LangGraph to raise an error
    async def mock_run_stream(*args, **kwargs):
        yield {
            "message": "Analyzing request...",
            "tool": None,
            "input": None,
            "output": None
        }
        raise Exception("Tool execution failed")
    
    with patch("src.api.agent_calendar.llm_selector", mock_llm_selector), \
         patch("src.api.agent_calendar.run_langgraph", mock_run_stream):
        
        response = client.post(
            "/api/v1/agent/calendar",
            json={
                "text": "Show me my calendar for tomorrow",
                "provider": "google"
            }
        )
        
        assert response.status_code == 200
        
        # Parse SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                event_data = line[6:]
                events.append(event_data)
        
        # Should have error in final response
        final_response = AgentResponse.parse_raw(events[-1])
        assert "Error" in final_response.summary 

def test_agent_health_check():
    """Test agent health check endpoint."""
    response = client.get("/api/v1/agent/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_intent_detection():
    """Test intent detection for various user inputs."""
    test_cases = [
        {
            "input": "Schedule a meeting with John tomorrow at 2pm",
            "expected_intent": "create_event",
            "expected_entities": {
                "participant": "John",
                "time": "tomorrow at 2pm"
            }
        },
        {
            "input": "What meetings do I have today?",
            "expected_intent": "list_events",
            "expected_entities": {
                "time": "today"
            }
        },
        {
            "input": "Cancel my 3pm meeting",
            "expected_intent": "delete_event",
            "expected_entities": {
                "time": "3pm"
            }
        }
    ]

    for test_case in test_cases:
        response = client.post(
            "/api/v1/agent/detect-intent",
            json={"text": test_case["input"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == test_case["expected_intent"]
        assert all(
            data["entities"].get(k) == v
            for k, v in test_case["expected_entities"].items()
        )

def test_agent_response_creation():
    """Test agent response creation for different intents."""
    test_cases = [
        {
            "intent": "create_event",
            "entities": {
                "summary": "Team Meeting",
                "start": "2024-01-01T14:00:00Z",
                "end": "2024-01-01T15:00:00Z"
            },
            "expected_status": 200
        },
        {
            "intent": "list_events",
            "entities": {
                "time": "today"
            },
            "expected_status": 200
        },
        {
            "intent": "delete_event",
            "entities": {
                "event_id": "test_event_id"
            },
            "expected_status": 200
        }
    ]

    for test_case in test_cases:
        response = client.post(
            "/api/v1/agent/respond",
            json={
                "intent": test_case["intent"],
                "entities": test_case["entities"]
            }
        )
        assert response.status_code == test_case["expected_status"]
        data = response.json()
        assert "response" in data
        assert "action" in data

def test_agent_error_handling():
    """Test agent error handling for invalid inputs."""
    test_cases = [
        {
            "input": "Invalid intent",
            "expected_status": 400
        },
        {
            "input": "",
            "expected_status": 400
        },
        {
            "input": None,
            "expected_status": 422
        }
    ]

    for test_case in test_cases:
        response = client.post(
            "/api/v1/agent/detect-intent",
            json={"text": test_case["input"]}
        )
        assert response.status_code == test_case["expected_status"]

def test_agent_context_management():
    """Test agent context management across multiple interactions."""
    # First interaction
    response1 = client.post(
        "/api/v1/agent/detect-intent",
        json={"text": "Schedule a meeting with John"}
    )
    assert response1.status_code == 200
    context_id = response1.json().get("context_id")
    assert context_id is not None

    # Follow-up interaction
    response2 = client.post(
        "/api/v1/agent/detect-intent",
        json={
            "text": "Make it tomorrow at 2pm",
            "context_id": context_id
        }
    )
    assert response2.status_code == 200
    assert response2.json().get("context_id") == context_id

def test_agent_prompt_templates():
    """Test agent prompt templates for different scenarios."""
    test_cases = [
        {
            "scenario": "create_event",
            "expected_template": "create_event_prompt"
        },
        {
            "scenario": "list_events",
            "expected_template": "list_events_prompt"
        },
        {
            "scenario": "delete_event",
            "expected_template": "delete_event_prompt"
        }
    ]

    for test_case in test_cases:
        response = client.get(
            f"/api/v1/agent/prompt-templates/{test_case['scenario']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["template_name"] == test_case["expected_template"]
        assert "template" in data

def test_agent_logging():
    """Test agent interaction logging."""
    # Make a test interaction
    response = client.post(
        "/api/v1/agent/detect-intent",
        json={"text": "What meetings do I have today?"}
    )
    assert response.status_code == 200
    interaction_id = response.json().get("interaction_id")
    assert interaction_id is not None

    # Check the log
    log_response = client.get(f"/api/v1/agent/logs/{interaction_id}")
    assert log_response.status_code == 200
    log_data = log_response.json()
    assert log_data["interaction_id"] == interaction_id
    assert "timestamp" in log_data
    assert "intent" in log_data
    assert "entities" in log_data

def test_agent_rate_limiting():
    """Test rate limiting on agent endpoints."""
    # Make multiple requests in quick succession
    for _ in range(settings.AGENT_RATE_LIMIT_PER_MINUTE + 1):
        response = client.post(
            "/api/v1/agent/detect-intent",
            json={"text": "Test message"}
        )
        if response.status_code == 429:
            break

    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"] 