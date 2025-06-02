"""
Main application module for Personal Calendar Assistant.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis

from app.api.router import router as api_router
from app.auth.router import router as auth_router
from app.config import get_settings
from app.db.mongodb import mongodb
from app.db.init_db import init_db

# Setup logging
logging.basicConfig(
    level=logging.getLevelName(get_settings().LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_redis():
    """
    Get Redis connection.
    """
    try:
        redis = Redis.from_url(get_settings().REDIS_URL)
        yield redis
    finally:
        redis.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handlers for application startup and shutdown.
    """
    # Startup: Initialize connections to external services
    logger.info("Starting up Personal Calendar Assistant")
    await mongodb.connect_to_database()
    await init_db()
    
    yield
    
    # Shutdown: Close connections to external services
    logger.info("Shutting down Personal Calendar Assistant")
    await mongodb.close_database_connection()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="An LLM-driven scheduling agent for calendar management",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    
    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint to verify the service is running.
        """
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "service": settings.APP_NAME},
        )
    
    # Simple health probe
    @app.get("/healthz", tags=["Health"])
    async def healthz():
        """
        Simple health probe for Kubernetes liveness check.
        """
        return {"status": "ok"}
    
    # Readiness probe
    @app.get("/readyz", tags=["Health"])
    async def readyz(redis: Redis = Depends(get_redis)):
        """
        Readiness probe that verifies MongoDB and Redis connections.
        """
        db_healthy = False
        redis_healthy = False
        
        # Check MongoDB connection
        try:
            await mongodb.client.admin.command('ping')
            db_healthy = True
        except Exception as e:
            logger.error(f"MongoDB healthcheck failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB connection failed",
            )
        
        # Check Redis connection
        try:
            redis.ping()
            redis_healthy = True
        except Exception as e:
            logger.error(f"Redis healthcheck failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection failed",
            )
        
        return {
            "status": "ready",
            "mongodb": db_healthy,
            "redis": redis_healthy
        }
    
    # Include API routers
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(api_router, prefix=settings.API_PREFIX, tags=["API"])
    
    return app


app = create_application()
