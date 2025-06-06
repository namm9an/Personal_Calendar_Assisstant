"""Tests for health check and rate limiting endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
import time

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_rate_limiting():
    """Test rate limiting on calendar endpoints."""
    # Make multiple requests in quick succession
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.get("/api/v1/calendar/events")
        if response.status_code == 429:
            break
        time.sleep(0.1)  # Small delay between requests
    
    # The last request should be rate limited
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]

def test_rate_limit_reset():
    """Test rate limit reset after waiting."""
    # Make some requests
    for _ in range(5):
        client.get("/api/v1/calendar/events")
        time.sleep(0.1)
    
    # Wait for rate limit to reset
    time.sleep(60)
    
    # Should be able to make requests again
    response = client.get("/api/v1/calendar/events")
    assert response.status_code != 429

def test_different_endpoints_rate_limits():
    """Test rate limits on different endpoints."""
    # Test calendar events endpoint
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.get("/api/v1/calendar/events")
        if response.status_code == 429:
            break
        time.sleep(0.1)
    assert response.status_code == 429

    # Test create event endpoint (should have separate rate limit)
    for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1):
        response = client.post("/api/v1/calendar/events", json={
            "summary": "Test Event",
            "start": "2024-01-01T10:00:00Z",
            "end": "2024-01-01T11:00:00Z"
        })
        if response.status_code == 429:
            break
        time.sleep(0.1)
    assert response.status_code == 429

def test_rate_limit_headers():
    """Test rate limit headers in response."""
    response = client.get("/api/v1/calendar/events")
    
    # Check for rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Verify header values
    assert int(response.headers["X-RateLimit-Limit"]) == settings.RATE_LIMIT_PER_MINUTE
    assert int(response.headers["X-RateLimit-Remaining"]) < settings.RATE_LIMIT_PER_MINUTE
    assert int(response.headers["X-RateLimit-Reset"]) > 0

def test_health_check_dependencies():
    """Test health check with dependency status."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    
    # Check all required dependencies
    assert "status" in data
    assert "dependencies" in data
    assert "mongodb" in data["dependencies"]
    assert "calendar_api" in data["dependencies"]
    
    # Verify dependency status
    assert data["dependencies"]["mongodb"]["status"] in ["healthy", "unhealthy"]
    assert data["dependencies"]["calendar_api"]["status"] in ["healthy", "unhealthy"]

def test_health_check_metrics():
    """Test health check metrics endpoint."""
    response = client.get("/health/metrics")
    assert response.status_code == 200
    data = response.json()
    
    # Check for required metrics
    assert "uptime" in data
    assert "memory_usage" in data
    assert "cpu_usage" in data
    assert "active_connections" in data
    
    # Verify metric types
    assert isinstance(data["uptime"], float)
    assert isinstance(data["memory_usage"], dict)
    assert isinstance(data["cpu_usage"], float)
    assert isinstance(data["active_connections"], int) 