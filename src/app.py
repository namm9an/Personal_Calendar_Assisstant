from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Callable
from src.db.connection import mongodb
from src.db.init_db import init_db
from src.repositories.mongodb_repository import MongoDBRepository
from src.core.config import settings
from src.core.exceptions import (
    DatabaseError,
    ValidationError,
    AuthenticationError,
    NotFoundError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up application...")
    try:
        await mongodb.connect_to_database()
        await init_db()
        logger.info("Application startup complete!")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await mongodb.close_database_connection()
    logger.info("Application shutdown complete!")

app = FastAPI(
    title="Personal Calendar Assistant",
    description="AI-powered calendar management system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Error handlers
@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "Database error occurred"}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    logger.error(f"Authentication error: {exc}")
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    logger.error(f"Not found error: {exc}")
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

# Dependency
async def get_repository():
    """Dependency for getting repository instance."""
    try:
        return MongoDBRepository()
    except Exception as e:
        logger.error(f"Failed to create repository: {e}")
        raise DatabaseError("Failed to create repository")

# Health check endpoints
@app.get("/healthz")
async def healthz():
    """Basic health check endpoint."""
    return {"status": "ok"}

@app.get("/readyz")
async def readyz(repo: MongoDBRepository = Depends(get_repository)):
    """Readiness check endpoint."""
    try:
        # Check MongoDB connection
        await mongodb.client.admin.command('ping')
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

# Import and include routers
from src.api.auth import router as auth_router
from src.api.calendar import router as calendar_router
from src.api.agent import router as agent_router

# Include routers with proper prefix and tags
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={401: {"description": "Unauthorized"}}
)

app.include_router(
    calendar_router,
    prefix="/api/v1/calendar",
    tags=["Calendar"],
    responses={401: {"description": "Unauthorized"}}
)

app.include_router(
    agent_router,
    prefix="/api/v1/agent",
    tags=["AI Agent"],
    responses={401: {"description": "Unauthorized"}}
) 