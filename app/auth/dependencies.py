"""
Authentication dependencies for the Personal Calendar Assistant.
"""
from datetime import datetime, timedelta
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.postgres import get_db
from app.models.user import User, UserInDB

# OAuth2 token URL for auth code flow
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/auth/login",
    tokenUrl="/auth/token",
)

settings = get_settings()


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str
    expires_at: datetime


class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        JWT token as string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
        
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, or None if not.
    
    Args:
        token: JWT token (optional)
        db: Database session
        
    Returns:
        User object or None
    """
    if token is None:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None or not user.is_active:
            return None
            
        return user
    except JWTError:
        return None
