"""
Authentication router for the Personal Calendar Assistant.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.config import Config

from app.auth.dependencies import Token, create_access_token
from app.config import get_settings
from app.db.postgres import get_db
from app.models.calendar import CalendarProvider, UserCalendar, UserCalendarCreate
from app.models.user import User, UserCreate

settings = get_settings()
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize OAuth client
config = Config(environ={"GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
                         "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET})
oauth = OAuth(config)

# Register Google OAuth
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": settings.GOOGLE_AUTH_SCOPES},
)


@router.get("/google/login")
async def login_via_google(request: Request):
    """
    Initiate Google OAuth login flow.
    
    This endpoint redirects the user to Google's OAuth consent screen.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle callback from Google OAuth.
    
    This endpoint exchanges the authorization code for tokens and creates/updates the user.
    """
    try:
        # Get token from Google
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from Google
        user_info = token.get("userinfo")
        if not user_info:
            resp = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo")
            user_info = resp.json()
        
        # Extract Google user details
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        
        # Extract tokens
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token")
        expires_at = datetime.utcnow() + timedelta(seconds=token.get("expires_in", 3600))
        
        # Find or create user
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Try to find by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Create new user
                user_create = UserCreate(email=email, name=name)
                user = User(**user_create.model_dump())
                user.google_id = google_id
                db.add(user)
            else:
                # Update existing user with Google ID
                user.google_id = google_id
        
        # Encrypt tokens before storing
        from app.services.encryption import TokenEncryption
        encryption_service = TokenEncryption()
        
        # Update Google tokens with encryption
        user.google_access_token = encryption_service.encrypt(access_token)
        user.google_refresh_token = encryption_service.encrypt(refresh_token) if refresh_token else user.google_refresh_token
        user.google_token_expiry = expires_at
        
        # Commit changes
        db.commit()
        db.refresh(user)
        
        # Fetch user calendars from Google - would be implemented in a service
        # fetch_and_save_google_calendars(user, db)
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )
        
        # Create token response
        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.utcnow() + access_token_expires,
        )
        
        # Set token in cookie and redirect to frontend
        response = RedirectResponse(url="/")
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=settings.ENVIRONMENT != "development",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
        return response
        
    except Exception as e:
        logger.exception(f"Error in Google OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get access token after authentication.
    
    This endpoint is called by the frontend after receiving the callback.
    """
    try:
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or "Bearer" not in auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Extract user ID from token
        token = auth_header.split("Bearer ")[1]
        user_id = get_user_id_from_token(token)
        
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Create new token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.utcnow() + access_token_expires,
        )
        
    except Exception as e:
        logger.exception(f"Error in token endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


@router.post("/logout")
async def logout():
    """
    Logout user by clearing cookies.
    """
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="access_token")
    return response


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        User ID as string
    """
    # This is a placeholder - actual implementation would decode the JWT
    # For now, let's return a dummy value
    return "user_id"
