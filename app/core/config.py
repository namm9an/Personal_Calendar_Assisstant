"""Configuration module."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings."""
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    
    # Microsoft OAuth settings
    MS_CLIENT_ID: str = os.getenv("MS_CLIENT_ID", "test_client_id")
    MS_CLIENT_SECRET: str = os.getenv("MS_CLIENT_SECRET", "test_client_secret")
    MS_TENANT_ID: str = os.getenv("MS_TENANT_ID", "test_tenant_id")
    MS_REDIRECT_URI: str = os.getenv("MS_REDIRECT_URI", "http://localhost:8000/auth/microsoft/callback")
    MS_AUTH_SCOPES: str = os.getenv("MS_AUTH_SCOPES", "Calendars.ReadWrite Calendars.Read")
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "test_client_id")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "test_client_secret")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    GOOGLE_AUTH_SCOPES: str = os.getenv("GOOGLE_AUTH_SCOPES", "https://www.googleapis.com/auth/calendar")
    
    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "test_calendar_db")
    
    # Redis settings
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://redis:6379/0")
    
    # Test settings
    TEST_BASE_URL: str = os.getenv("TEST_BASE_URL", "http://localhost:8000")
    TEST_NAMESPACE: str = os.getenv("TEST_NAMESPACE", "production")
    
    # Monitoring settings
    GRAFANA_URL: str = os.getenv("GRAFANA_URL", "http://localhost:3000")
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    
    # JWT settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your_jwt_secret_key_here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: str = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    
    # LLM settings
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "your_llm_api_key")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1")
    
    # Security settings
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

settings = Settings() 