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
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.models.mongodb_models import User
from app.services.encryption import TokenEncryption
from app.core.exceptions import OAuthError

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure SSL certificate bundle
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

class MicrosoftOAuthService:
    """Service for handling Microsoft OAuth authentication and token management."""
    
    def __init__(self, db: AsyncIOMotorDatabase, user: Optional[User] = None):
        """
        Initialize the Microsoft OAuth service.
        
        Args:
            db: MongoDB database
            user: User object (optional)
        """
        self.db = db
        self.user = user
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
    
    async def save_user_tokens(self, user_id: str, token_data: Dict) -> User:
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
            # Find user in MongoDB
            user_doc = await self.db.users.find_one({"_id": user_id})
            if not user_doc:
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
            encrypted_access_token = self.encryption_service.encrypt(access_token)
            encrypted_refresh_token = self.encryption_service.encrypt(refresh_token)
            
            # Extract Microsoft user ID (object ID) from claims
            ms_id = None
            if "id_token_claims" in token_data:
                ms_id = token_data["id_token_claims"].get("oid")  # Object ID
            
            # Update user document
            update_data = {
                "microsoft_access_token": encrypted_access_token,
                "microsoft_refresh_token": encrypted_refresh_token,
                "microsoft_token_expiry": expiry_time,
                "updated_at": datetime.utcnow()
            }
            
            if ms_id:
                update_data["microsoft_id"] = ms_id
                
            # Update in MongoDB
            result = await self.db.users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                logger.warning(f"No changes made to user {user_id}")
            
            # Get updated user
            updated_user_doc = await self.db.users.find_one({"_id": user_id})
            return User(**updated_user_doc)
            
        except Exception as e:
            logger.error(f"Error saving Microsoft tokens for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to save Microsoft tokens: {str(e)}")
    
    async def get_tokens(self, user_id: str) -> Tuple[str, str, datetime]:
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
            # Find user in MongoDB
            user_doc = await self.db.users.find_one({"_id": user_id})
            if not user_doc:
                logger.error(f"User not found: {user_id}")
                raise OAuthError("User not found")
            
            user = User(**user_doc)
            
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
                encrypted_access_token = self.encryption_service.encrypt(access_token)
                encrypted_refresh_token = self.encryption_service.encrypt(refresh_token)
                
                # Update in MongoDB
                await self.db.users.update_one(
                    {"_id": user_id},
                    {"$set": {
                        "microsoft_access_token": encrypted_access_token,
                        "microsoft_refresh_token": encrypted_refresh_token,
                        "microsoft_token_expiry": expiry_time,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                return access_token, refresh_token, expiry_time
            
            return access_token, refresh_token, user.microsoft_token_expiry
        except Exception as e:
            logger.error(f"Error getting Microsoft tokens for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to get Microsoft tokens: {str(e)}")
    
    async def save_state(self, state: str, user_id: str) -> None:
        """
        Save OAuth state parameter for CSRF protection.
        
        Args:
            state: State parameter
            user_id: ID of the user
        """
        # In a real implementation, this would save to a secure store
        # For testing, we'll just store in memory
        if os.getenv('TESTING', '').lower() == 'true':
            from app.services.oauth_service import oauth_states
            oauth_states[state] = {
                "user_id": user_id,
                "expires": datetime.utcnow() + timedelta(minutes=10)
            }
        else:
            # In production, save to database
            await self.db.oauth_states.insert_one({
                "state": state,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "expires": datetime.utcnow() + timedelta(minutes=10)
            })
    
    async def validate_state(self, state: str) -> str:
        """
        Validate OAuth state parameter and return associated user ID.
        
        Args:
            state: State parameter to validate
            
        Returns:
            User ID associated with the state
            
        Raises:
            OAuthError: If state is invalid or expired
        """
        if os.getenv('TESTING', '').lower() == 'true':
            from app.services.oauth_service import oauth_states
            state_data = oauth_states.get(state)
            if not state_data:
                raise OAuthError("Invalid OAuth state")
            
            if state_data["expires"] < datetime.utcnow():
                oauth_states.pop(state, None)
                raise OAuthError("OAuth state expired")
            
            # Remove state after use
            user_id = state_data["user_id"]
            oauth_states.pop(state, None)
            return user_id
        else:
            # In production, validate from database
            state_doc = await self.db.oauth_states.find_one({"state": state})
            if not state_doc:
                raise OAuthError("Invalid OAuth state")
            
            if state_doc["expires"] < datetime.utcnow():
                await self.db.oauth_states.delete_one({"state": state})
                raise OAuthError("OAuth state expired")
            
            # Remove state after use
            user_id = state_doc["user_id"]
            await self.db.oauth_states.delete_one({"state": state})
            return user_id
    
    async def get_token(self, code: str, user_id: str) -> dict:
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
            await self.save_user_tokens(user_id, token_data)
            
            return token_data
        except Exception as e:
            logger.error(f"Error getting token for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to get token: {str(e)}")
