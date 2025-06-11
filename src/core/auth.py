from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from .config import settings
import os

# JWT Settings
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Extract token from either cookie or header
async def get_token_from_request(request: Request) -> Optional[str]:
    # Try to get from cookie first
    token = request.cookies.get("access_token")
    
    # If it's in the cookie with Bearer prefix
    if token and token.startswith("Bearer "):
        return token.split(" ")[1]
    
    # If it's just the token in the cookie
    if token:
        return token
    
    # Otherwise try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    return None

async def get_current_user(request: Request):
    """Get the currently authenticated user from the request."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = await get_token_from_request(request)
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    from ..db.connection import mongodb
    user = await mongodb.db.users.find_one({"_id": user_id})
    
    if user is None:
        raise credentials_exception
    
    return user 