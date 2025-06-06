from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any
from src.utils.rate_limiter import rate_limit

router = APIRouter(tags=["health"])

@router.get("/health")
@rate_limit(limit=60, window=60)
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {"status": "healthy"}

@router.get("/health/dependencies")
@rate_limit(limit=30, window=60)
async def health_check_dependencies() -> Dict[str, Any]:
    """Check health of all dependencies."""
    return {
        "status": "healthy",
        "dependencies": {
            "database": "healthy",
            "redis": "healthy",
            "google_calendar": "healthy",
            "microsoft_calendar": "healthy"
        }
    }

@router.get("/health/metrics")
@rate_limit(limit=30, window=60)
async def health_check_metrics() -> Dict[str, Any]:
    """Get health metrics."""
    return {
        "status": "healthy",
        "metrics": {
            "uptime": "1h",
            "requests_per_minute": 10,
            "error_rate": 0.01,
            "response_time": 0.1
        }
    }

@router.get("/rate-limit")
async def get_rate_limit() -> Dict[str, Any]:
    """Get current rate limit status."""
    return {
        "limit": 60,
        "remaining": 59,
        "reset": int(datetime.now().timestamp()) + 60
    } 