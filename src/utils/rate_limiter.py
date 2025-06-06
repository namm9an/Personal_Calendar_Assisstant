from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from functools import wraps
import time
from typing import Callable, Dict, Any
import redis.asyncio as redis
from src.core.config import settings
from datetime import datetime, timedelta

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL)

# In-memory storage for rate limiting
rate_limit_store: Dict[str, Dict[str, Any]] = {}

def rate_limit(limit: int = 60, window: int = 60):
    """Rate limiting decorator.
    
    Args:
        limit: Number of requests allowed in the window
        window: Time window in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object from kwargs
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                return await func(*args, **kwargs)
            
            # Get client IP
            client_ip = request.client.host
            now = datetime.now()
            
            # Initialize or get rate limit data for this IP
            if client_ip not in rate_limit_store:
                rate_limit_store[client_ip] = {
                    'count': 0,
                    'window_start': now,
                    'reset_time': now + timedelta(seconds=window)
                }
            
            # Check if window has expired
            if now > rate_limit_store[client_ip]['reset_time']:
                rate_limit_store[client_ip] = {
                    'count': 0,
                    'window_start': now,
                    'reset_time': now + timedelta(seconds=window)
                }
            
            # Increment count
            rate_limit_store[client_ip]['count'] += 1
            
            # Check if limit exceeded
            if rate_limit_store[client_ip]['count'] > limit:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        'X-RateLimit-Limit': str(limit),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(rate_limit_store[client_ip]['reset_time'].timestamp()))
                    }
                )
            
            # Add rate limit headers
            response = await func(*args, **kwargs)
            if isinstance(response, dict):
                response['headers'] = {
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': str(limit - rate_limit_store[client_ip]['count']),
                    'X-RateLimit-Reset': str(int(rate_limit_store[client_ip]['reset_time'].timestamp()))
                }
            return response
        
        return wrapper
    return decorator 