from datetime import datetime
from src.utils.token_encryption import TokenEncryption
from src.models.user import User
from src.db.test_config import TestingSessionLocal
from cryptography.fernet import InvalidToken

class OAuthService:
    def __init__(self):
        self.token_encryption = TokenEncryption()

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
                user.google_token_expiry = self.token_encryption.get_token_expiry(provider)
            elif provider == "microsoft":
                user.microsoft_access_token = self.token_encryption.encrypt(access_token)
                if refresh_token:
                    user.microsoft_refresh_token = self.token_encryption.encrypt(refresh_token)
                user.microsoft_token_expiry = self.token_encryption.get_token_expiry(provider)

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