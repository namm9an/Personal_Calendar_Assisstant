from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from src.db.connection import mongodb
from src.db.init_db import init_db
from src.repositories.mongodb_repository import MongoDBRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    await mongodb.connect_to_database()
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await mongodb.close_database_connection()

app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
async def get_repository():
    return MongoDBRepository()

# Health check endpoints
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz(repo: MongoDBRepository = Depends(get_repository)):
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

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(calendar_router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"]) 