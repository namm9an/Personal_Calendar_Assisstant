from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Callable
from db.connection import mongodb
from db.init_db import init_db
from repositories.mongodb_repository import MongoDBRepository
from core.config import settings
from core.exceptions import (
    DatabaseError,
    ValidationError,
    AuthenticationError,
    NotFoundError
)
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2AuthorizationCodeBearer
from datetime import datetime

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
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
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

# Health check endpoint
@app.get("/healthz", status_code=200)
async def health_check():
    """
    Health check endpoint for monitoring and deployment.
    Returns basic system information and status.
    """
    try:
        # Check MongoDB connection
        await mongodb.db.command("ping")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
        
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": db_status,
        "uptime": time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0
    }

# Startup event to record application start time
@app.on_event("startup")
async def startup_event():
    app.state.start_time = time.time()
    logger.info("Application starting up")

# Import and include routers
from api.auth import router as auth_router
from api.agent_calendar import router as calendar_router

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

# Custom OpenAPI docs
@app.get("/api/docs", include_in_schema=False)
async def get_swagger_documentation():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Personal Calendar Assistant API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    )

# Error handler for all exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    ) 