"""
Microsoft OAuth service for handling authentication and token management.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import os
import certifi

import msal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from msal import ConfidentialClientApplication

from app.config import get_settings
from app.models.user import User
from app.services.encryption import TokenEncryption
from app.core.exceptions import OAuthError

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure SSL certificate bundle
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

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
        self.validate_authority = not os.getenv('TESTING', '').lower() == 'true'
        
        # Test mode configuration
        if os.getenv('TESTING', '').lower() == 'true':
            self.authority = os.getenv('MS_AUTHORITY', self.authority)
            self.token_endpoint = os.getenv('MS_TOKEN_ENDPOINT', f"{self.authority}/oauth2/v2.0/token")
            self.authorize_endpoint = os.getenv('MS_AUTHORIZE_ENDPOINT', f"{self.authority}/oauth2/v2.0/authorize")
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Generate Microsoft OAuth authorization URL with state parameter.
        
        Returns:
            Tuple containing the authorization URL and state parameter
            
        Raises:
            OAuthError: If authorization URL generation fails
        """
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
                validate_authority=self.validate_authority,
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
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise OAuthError(f"Failed to generate authorization URL: {str(e)}")
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Microsoft OAuth callback
            
        Returns:
            Dict containing token information including access_token, refresh_token,
            and expiration time
            
        Raises:
            OAuthError: If token exchange fails
        """
        try:
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
                validate_authority=self.validate_authority,
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
                raise OAuthError(f"Failed to get Microsoft token: {result.get('error_description')}")
                
            return result
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise OAuthError(f"Failed to exchange code for token: {str(e)}")
    
    def save_user_tokens(self, user_id: str, token_data: Dict) -> User:
        """
        Save Microsoft OAuth tokens for a user with encryption.
        
        Args:
            user_id: ID of the user
            token_data: Token data from Microsoft OAuth
            
        Returns:
            Updated user object
            
        Raises:
            OAuthError: If user not found or token saving fails
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                raise OAuthError("User not found")
                
            # Extract tokens
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)
            
            if not access_token or not refresh_token:
                raise OAuthError("Invalid token data: missing access or refresh token")
            
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
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving Microsoft tokens for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to save Microsoft tokens: {str(e)}")
    
    def get_tokens(self, user_id: str) -> Tuple[str, str, datetime]:
        """
        Get Microsoft OAuth tokens for a user, refreshing if needed.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple containing access_token, refresh_token, and expiry time
            
        Raises:
            OAuthError: If user not found or has no Microsoft credentials
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                raise OAuthError("User not found")
                
            if not user.microsoft_access_token or not user.microsoft_refresh_token:
                logger.error(f"User {user_id} has no Microsoft credentials")
                raise OAuthError("No Microsoft credentials found for user")
                
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
                    validate_authority=self.validate_authority,
                )
                
                result = app.acquire_token_by_refresh_token(
                    refresh_token=refresh_token,
                    scopes=self.scopes,
                )
                
                if "error" in result:
                    logger.error(f"Error refreshing token: {result.get('error_description')}")
                    raise OAuthError(f"Failed to refresh token: {result.get('error_description')}")
                
                # Update tokens
                access_token = result["access_token"]
                refresh_token = result.get("refresh_token", refresh_token)
                expires_in = result.get("expires_in", 3600)
                expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Save updated tokens
                user.microsoft_access_token = self.encryption_service.encrypt(access_token)
                user.microsoft_refresh_token = self.encryption_service.encrypt(refresh_token)
                user.microsoft_token_expiry = expiry_time
                
                self.db.commit()
                self.db.refresh(user)
            
            return access_token, refresh_token, user.microsoft_token_expiry
        except Exception as e:
            logger.error(f"Error getting Microsoft tokens for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to get Microsoft tokens: {str(e)}")
    
    def save_state(self, state: str, user_id: str) -> None:
        """
        Save OAuth state parameter for CSRF protection.
        
        Args:
            state: State parameter
            user_id: ID of the user
        """
        # In a real implementation, this would save to a secure store
        # For testing, we'll just store in memory
        if os.getenv('TESTING', '').lower() == 'true':
            self._test_states = getattr(self, '_test_states', {})
            self._test_states[state] = user_id
    
    def validate_state(self, state: str) -> str:
        """
        Validate OAuth state parameter.
        
        Args:
            state: State parameter to validate
            
        Returns:
            User ID associated with the state
            
        Raises:
            OAuthError: If state is invalid
        """
        if os.getenv('TESTING', '').lower() == 'true':
            self._test_states = getattr(self, '_test_states', {})
            if state not in self._test_states:
                raise OAuthError("Invalid state parameter")
            return self._test_states.pop(state)
        else:
            # In a real implementation, this would validate against a secure store
            raise NotImplementedError("State validation not implemented for production")
    
    def get_token(self, code: str, user_id: str) -> dict:
        """
        Get Microsoft OAuth token for a user.
        
        Args:
            code: Authorization code
            user_id: ID of the user
            
        Returns:
            Token data
            
        Raises:
            OAuthError: If token retrieval fails
        """
        try:
            # Exchange code for token
            token_data = self.exchange_code_for_token(code)
            
            # Save tokens for user
            self.save_user_tokens(user_id, token_data)
            
            return token_data
        except Exception as e:
            logger.error(f"Error getting token for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to get token: {str(e)}")
