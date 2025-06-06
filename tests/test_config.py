"""Test configuration for the Personal Calendar Assistant."""

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Test database configuration
TEST_MONGODB_URI = "mongodb://localhost:27017"
TEST_MONGODB_DB_NAME = "test_calendar_db"

# Test environment variables
TEST_ENV_VARS = {
    "MONGODB_URI": TEST_MONGODB_URI,
    "MONGODB_DB_NAME": TEST_MONGODB_DB_NAME,
    "TESTING": "true",
    "REDIS_URL": "redis://localhost:6379",
    "SECRET_KEY": "test_secret_key",
    "GOOGLE_CLIENT_ID": "test_google_client_id",
    "GOOGLE_CLIENT_SECRET": "test_google_client_secret",
    "GOOGLE_REDIRECT_URI": "http://localhost:8000/auth/google/callback",
    "GOOGLE_AUTH_SCOPES": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events",
    "MS_CLIENT_ID": "test_ms_client_id",
    "MS_CLIENT_SECRET": "test_ms_client_secret",
    "MS_TENANT_ID": "test_ms_tenant_id",
    "MS_REDIRECT_URI": "http://localhost:8000/auth/microsoft/callback",
    "MS_AUTH_SCOPES": "Calendars.ReadWrite User.Read",
    "TOKEN_ENCRYPTION_KEY": "test_token_encryption_key",
    "GEMINI_API_KEY": "test_gemini_api_key",
    "DEFAULT_LLM_MODEL": "gemini-pro",
    "FALLBACK_LLM_MODEL": "local-llama",
    "DEFAULT_WORKING_HOURS_START": "09:00",
    "DEFAULT_WORKING_HOURS_END": "17:00",
    "DEFAULT_TIMEZONE": "UTC",
    "ENABLE_PROMETHEUS": "true",
    "RATE_LIMIT_PER_MINUTE": "60",
    "AGENT_RATE_LIMIT_PER_MINUTE": "30",
    # Test-specific settings
    "MS_VALIDATE_AUTHORITY": "false",
    "MS_AUTHORITY": "https://login.microsoftonline.com/test_tenant_id",
    "MS_INSTANCE": "https://login.microsoftonline.com/",
    "MS_TOKEN_ENDPOINT": "https://login.microsoftonline.com/test_tenant_id/oauth2/v2.0/token",
    "MS_AUTHORIZE_ENDPOINT": "https://login.microsoftonline.com/test_tenant_id/oauth2/v2.0/authorize"
}

# Test data
TEST_USER_DATA = {
    "email": "test@example.com",
    "name": "Test User",
    "timezone": "UTC",
    "working_hours_start": "09:00",
    "working_hours_end": "17:00",
    "preferences": {
        "default_calendar": "primary",
        "notification_enabled": True
    }
}

# Base datetime for test events
BASE_DATETIME = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

TEST_EVENT_DATA = {
    "summary": "Test Event",
    "description": "Test Description",
    "start_datetime": BASE_DATETIME + timedelta(hours=1),
    "end_datetime": BASE_DATETIME + timedelta(hours=2),
    "timezone": "UTC",
    "location": "Test Location",
    "attendees": ["attendee@example.com"],
    "created_by": "test@example.com",
    "status": "confirmed"
}

TEST_SESSION_DATA = {
    "provider": "google",
    "access_token": "test_access_token",
    "refresh_token": "test_refresh_token",
    "token_type": "Bearer",
    "expires_at": BASE_DATETIME + timedelta(hours=1),
    "is_active": True,
    "scope": ["https://www.googleapis.com/auth/calendar"]
}

TEST_AGENT_LOG_DATA = {
    "intent": "list_events",
    "entities": {"date": "2025-06-10"},
    "response": "Found 3 events",
    "processing_time": 0.5,
    "success": True
}

def setup_test_environment():
    """Set up test environment variables."""
    # Store original environment variables
    original_env = {}
    for key in TEST_ENV_VARS:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment variables
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value
    
    return original_env

def teardown_test_environment():
    """Clean up test environment variables."""
    for key in TEST_ENV_VARS:
        if key in os.environ:
            del os.environ[key]

def get_test_db_uri():
    """Get test database URI."""
    return f"{TEST_MONGODB_URI}/{TEST_MONGODB_DB_NAME}"

def get_test_redis_uri():
    """Get test Redis URI."""
    return TEST_ENV_VARS["REDIS_URL"]

def get_test_ms_config():
    """Get Microsoft test configuration."""
    return {
        "client_id": TEST_ENV_VARS["MS_CLIENT_ID"],
        "client_secret": TEST_ENV_VARS["MS_CLIENT_SECRET"],
        "tenant_id": TEST_ENV_VARS["MS_TENANT_ID"],
        "authority": TEST_ENV_VARS["MS_AUTHORITY"],
        "validate_authority": TEST_ENV_VARS["MS_VALIDATE_AUTHORITY"].lower() == "true",
        "token_endpoint": TEST_ENV_VARS["MS_TOKEN_ENDPOINT"],
        "authorize_endpoint": TEST_ENV_VARS["MS_AUTHORIZE_ENDPOINT"]
    } 