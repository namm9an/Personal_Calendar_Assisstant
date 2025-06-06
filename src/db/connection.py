from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # MongoDB Settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URL")
    DATABASE_NAME: str = Field(default="calendar_db", description="MongoDB database name")
    MONGODB_MAX_POOL_SIZE: int = Field(default=100, description="Maximum connection pool size")
    MONGODB_MIN_POOL_SIZE: int = Field(default=10, description="Minimum connection pool size")
    MONGODB_MAX_IDLE_TIME_MS: int = Field(default=30000, description="Maximum idle time for connections")
    MONGODB_CONNECT_TIMEOUT_MS: int = Field(default=20000, description="Connection timeout in milliseconds")
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = Field(default=5000, description="Server selection timeout in milliseconds")

    # Redis Settings
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # Test Settings
    TEST_BASE_URL: str = Field(default="http://localhost:8000", description="Base URL for tests")
    TEST_NAMESPACE: str = Field(default="production", description="Test namespace")

    # Monitoring Settings
    GRAFANA_URL: str = Field(default="http://localhost:3000", description="Grafana URL")
    PROMETHEUS_URL: str = Field(default="http://localhost:9090", description="Prometheus URL")

    # JWT Settings
    JWT_SECRET: str = Field(default="your-secret-key-here", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")

    # OAuth Settings
    GOOGLE_CLIENT_ID: str = Field(default="test_google_client_id", description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="test_google_client_secret", description="Google OAuth client secret")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/auth/google/callback", description="Google OAuth redirect URI")

    # LLM Settings
    LLM_API_KEY: str = Field(default="your_llm_api_key", description="LLM API key")
    LLM_API_URL: str = Field(default="https://api.openai.com/v1", description="LLM API URL")

    # Microsoft OAuth Settings
    MS_CLIENT_ID: str = Field(default="test_ms_client_id", description="Microsoft OAuth client ID")
    MS_CLIENT_SECRET: str = Field(default="test_ms_client_secret", description="Microsoft OAuth client secret")
    MS_TENANT_ID: str = Field(default="test_ms_tenant_id", description="Microsoft tenant ID")
    TOKEN_ENCRYPTION_KEY: str = Field(default="test_token_encryption_key", description="Token encryption key")
    GEMINI_API_KEY: str = Field(default="test_gemini_api_key", description="Gemini API key")

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"  # Allow extra fields in environment variables
    }

settings = Settings()

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    _lock = asyncio.Lock()

    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def connect_to_database(cls):
        """Create database connection with retry logic."""
        async with cls._lock:
            if cls.client is not None:
                return

            try:
                cls.client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                    minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                    maxIdleTimeMS=settings.MONGODB_MAX_IDLE_TIME_MS,
                    connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
                    serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS
                )
                cls.db = cls.client[settings.DATABASE_NAME]
                
                # Verify connection
                await cls.client.admin.command('ping')
                logger.info("Successfully connected to MongoDB!")
                
                # Create indexes
                await cls._create_indexes()
                
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                if cls.client:
                    cls.client.close()
                    cls.client = None
                raise

    @classmethod
    async def _create_indexes(cls):
        """Create necessary indexes for collections."""
        try:
            # Users collection indexes
            await cls.db.users.create_index("email", unique=True)
            await cls.db.users.create_index("google_id")
            await cls.db.users.create_index("microsoft_id")
            
            # Events collection indexes
            await cls.db.events.create_index([("user_id", 1), ("start", 1)])
            await cls.db.events.create_index("start")
            await cls.db.events.create_index("end")
            
            logger.info("Successfully created MongoDB indexes")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise

    @classmethod
    async def close_database_connection(cls):
        """Close database connection."""
        async with cls._lock:
            if cls.client:
                cls.client.close()
                cls.client = None
                logger.info("Closed MongoDB connection!")

    @classmethod
    async def get_database(cls):
        """Get database instance with connection check."""
        if cls.client is None:
            await cls.connect_to_database()
        return cls.db

# Create global instance
mongodb = MongoDB() 