"""
Configuration settings for the Personal Calendar Assistant.
"""
from functools import lru_cache
from typing import List, Optional, Union

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, AnyHttpUrl


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "Personal Calendar Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "test_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["http://localhost:8000", "http://localhost:3000"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string to list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "calendar_assistant"
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Construct database URL if not provided."""
        if isinstance(v, str):
            return v
        return values.data.get("MONGODB_URI")
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        """Construct Redis URL if not provided."""
        if isinstance(v, str):
            return v
        return f"redis://{values.data.get('REDIS_HOST')}:{values.data.get('REDIS_PORT')}/{values.data.get('REDIS_DB')}"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = "test_google_client_id"
    GOOGLE_CLIENT_SECRET: str = "test_google_client_secret"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    GOOGLE_AUTH_SCOPES: str = "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events"
    
    # Microsoft OAuth
    MS_CLIENT_ID: str = "test_ms_client_id"
    MS_CLIENT_SECRET: str = "test_ms_client_secret"
    MS_TENANT_ID: str = "test_ms_tenant_id"
    MS_REDIRECT_URI: str = "http://localhost:8000/auth/microsoft/callback"
    MS_AUTH_SCOPES: str = "Calendars.ReadWrite User.Read"
    
    # Token Encryption
    TOKEN_ENCRYPTION_KEY: str = "test_token_encryption_key"
    
    # LLM settings
    GEMINI_API_KEY: str = "test_gemini_api_key"
    DEFAULT_LLM_MODEL: str = "gemini-pro"
    FALLBACK_LLM_MODEL: str = "local-llama"
    
    # Working hours
    DEFAULT_WORKING_HOURS_START: str = "09:00"
    DEFAULT_WORKING_HOURS_END: str = "17:00"
    DEFAULT_TIMEZONE: str = "UTC"
    
    # Monitoring
    ENABLE_PROMETHEUS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    AGENT_RATE_LIMIT_PER_MINUTE: int = 30
    
    # Calendar Settings
    DEFAULT_CALENDAR_ID: str = "primary"
    
    # OAuth Settings
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


@lru_cache()
def get_settings() -> Settings:
    """Create cached settings instance."""
    return Settings()

settings = Settings()
