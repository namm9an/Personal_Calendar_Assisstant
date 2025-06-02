"""
Microsoft OAuth service for handling authentication and token management.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import msal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User
from app.services.encryption import TokenEncryption

settings = get_settings()
logger = logging.getLogger(__name__)


class MicrosoftOAuthService:
    """Service for handling Microsoft OAuth authentication and token management."""
    
    def __init__(self, db: Session):
        """
        Initialize the Microsoft OAuth service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.client_id = settings.MS_CLIENT_ID
        self.client_secret = settings.MS_CLIENT_SECRET
        self.tenant_id = settings.MS_TENANT_ID
        self.redirect_uri = settings.MS_REDIRECT_URI
        self.scopes = settings.MS_AUTH_SCOPES.split()
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.encryption_service = TokenEncryption()
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Generate Microsoft OAuth authorization URL with state parameter.
        
        Returns:
            Tuple containing the authorization URL and state parameter
        """
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
        )
        
        # Generate a state parameter to prevent CSRF
        from secrets import token_urlsafe
        state = token_urlsafe(32)
        
        auth_url = app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state,
        )
        
        return auth_url, state
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Microsoft OAuth callback
            
        Returns:
            Dict containing token information including access_token, refresh_token,
            and expiration time
            
        Raises:
            HTTPException: If token exchange fails
        """
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
        )
        
        # Exchange authorization code for tokens
        result = app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )
        
        # Check for errors
        if "error" in result:
            logger.error(f"Error getting token: {result.get('error_description')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Microsoft token: {result.get('error_description')}",
            )
            
        return result
    
    def save_user_tokens(self, user_id: str, token_data: Dict) -> User:
        """
        Save Microsoft OAuth tokens for a user with encryption.
        
        Args:
            user_id: ID of the user
            token_data: Token data from Microsoft OAuth
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        # Extract tokens
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        
        # Calculate expiry time
        expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Encrypt tokens before storing
        user.microsoft_access_token = self.encryption_service.encrypt(access_token)
        user.microsoft_refresh_token = self.encryption_service.encrypt(refresh_token)
        user.microsoft_token_expiry = expiry_time
        
        # Extract Microsoft user ID (object ID) from claims
        if "id_token_claims" in token_data:
            ms_id = token_data["id_token_claims"].get("oid")  # Object ID
            if ms_id:
                user.microsoft_id = ms_id
                
        # Commit changes
        try:
            self.db.commit()
            self.db.refresh(user)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving Microsoft tokens for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save Microsoft tokens: {str(e)}",
            )
            
        return user
    
    def get_tokens(self, user_id: str) -> Tuple[str, str, datetime]:
        """
        Get Microsoft OAuth tokens for a user, refreshing if needed.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple containing access_token, refresh_token, and expiry time
            
        Raises:
            HTTPException: If user not found or has no Microsoft credentials
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        if not user.microsoft_access_token or not user.microsoft_refresh_token:
            logger.error(f"User {user_id} has no Microsoft credentials")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Microsoft credentials found for user",
            )
            
        # Decrypt tokens
        access_token = self.encryption_service.decrypt(user.microsoft_access_token)
        refresh_token = self.encryption_service.decrypt(user.microsoft_refresh_token)
        
        # Check if token is expired or about to expire (within 5 minutes)
        if user.microsoft_token_expiry <= datetime.utcnow() + timedelta(minutes=5):
            # Refresh the token
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
            )
            
            result = app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes,
            )
            
            if "error" in result:
                logger.error(f"Error refreshing token: {result.get('error_description')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to refresh Microsoft token: {result.get('error_description')}",
                )
                
            # Update tokens with encryption
            access_token = result.get("access_token")
            new_refresh_token = result.get("refresh_token", refresh_token)
            expires_in = result.get("expires_in", 3600)
            expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
            
            user.microsoft_access_token = self.encryption_service.encrypt(access_token)
            user.microsoft_refresh_token = self.encryption_service.encrypt(new_refresh_token)
            user.microsoft_token_expiry = expiry_time
            
            try:
                self.db.commit()
                self.db.refresh(user)
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error saving refreshed Microsoft tokens for user {user_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save refreshed Microsoft tokens: {str(e)}",
                )
                
            refresh_token = new_refresh_token
        
        return access_token, refresh_token, user.microsoft_token_expiry
