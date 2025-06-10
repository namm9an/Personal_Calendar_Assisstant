"""OAuth service for handling authentication."""
import json
import secrets
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple

import httpx
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from src.core.exceptions import ValidationError, AuthenticationError
from src.utils.token_encryption import TokenEncryption
from app.db.mongodb import mongodb
from app.models.mongodb_models import User

# Dictionary to store OAuth states
oauth_states: Dict[str, Dict] = {}

class OAuthService:
    """Service for handling OAuth authentication."""
    
    def __init__(self):
        """Initialize the OAuth service."""
        self.token_encryption = TokenEncryption.get_instance()
        self.db = mongodb.db

    async def get_user_by_id(self, user_id: str):
        """Get a user by their ID."""
        try:
            user_data = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user_data:
                return None
            return user_data
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    def create_or_update_user_tokens(self, email: str, provider: str, access_token: str, refresh_token: str = None) -> User:
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email)
                db.add(user)

            if provider == "google":
                user.google_access_token = self.token_encryption.encrypt(access_token)
                if refresh_token:
                    user.google_refresh_token = self.token_encryption.encrypt(refresh_token)
                user.google_token_expiry = datetime.utcnow() + timedelta(hours=1)
            elif provider == "microsoft":
                user.microsoft_access_token = self.token_encryption.encrypt(access_token)
                if refresh_token:
                    user.microsoft_refresh_token = self.token_encryption.encrypt(refresh_token)
                user.microsoft_token_expiry = datetime.utcnow() + timedelta(hours=1)

            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    def get_user_tokens(self, user_id: str, provider: str) -> tuple:
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, None

            try:
                if provider == "google":
                    access_token = self.token_encryption.decrypt(user.google_access_token)
                    refresh_token = self.token_encryption.decrypt(user.google_refresh_token)
                    expiry = user.google_token_expiry
                elif provider == "microsoft":
                    access_token = self.token_encryption.decrypt(user.microsoft_access_token)
                    refresh_token = self.token_encryption.decrypt(user.microsoft_refresh_token)
                    expiry = user.microsoft_token_expiry
                else:
                    return None, None
            except InvalidToken:
                return None, None

            if not access_token or (expiry and expiry < datetime.utcnow()):
                return None, None

            return access_token, refresh_token
        finally:
            db.close()
            
    async def save_state(self, state: str, user_id: str, provider: str) -> None:
        """Save OAuth state for validation."""
        oauth_states[state] = {
            "user_id": user_id,
            "provider": provider,
            "created_at": datetime.utcnow()
        }
        
    async def validate_state(self, state: str) -> Optional[Dict]:
        """Validate OAuth state and return state data if valid."""
        if state not in oauth_states:
            return None
            
        state_data = oauth_states[state]
        # Check if state is expired (30 minutes)
        if (datetime.utcnow() - state_data["created_at"]).total_seconds() > 1800:
            del oauth_states[state]
            return None
            
        # Remove state after successful validation
        del oauth_states[state]
        return state_data 