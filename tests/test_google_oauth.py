"""Tests for Google OAuth service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from app.services.google_oauth import GoogleOAuthService
from app.services.encryption import TokenEncryption
from app.core.exceptions import OAuthError

@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption

@pytest.fixture
def google_oauth_service(mock_token_encryption, test_db):
    """Create a Google OAuth service with mocked dependencies."""
    with patch("app.services.google_oauth.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.google_oauth.settings") as mock_settings:
            mock_settings.google_client_id = "test-client-id"
            mock_settings.google_client_secret = "test-client-secret"
            mock_settings.google_redirect_uri = "http://localhost:8000/auth/google/callback"
            mock_settings.google_auth_scopes = "https://www.googleapis.com/auth/calendar"
            mock_settings.token_encryption_key = "test-encryption-key"
            service = GoogleOAuthService(test_db)
            return service

class TestGoogleOAuthService:
    """Tests for GoogleOAuthService."""

    def test_google_authorization_url(self, google_oauth_service):
        """Test Google authorization URL generation."""
        url = google_oauth_service.get_authorization_url()
        
        # Verify URL components
        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http://localhost:8000/auth/google/callback" in url
        assert "scope=https://www.googleapis.com/auth/calendar" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
        assert "state=" in url  # Verify state parameter is present

    @patch("app.services.google_oauth.requests.post")
    async def test_google_token_exchange(self, mock_post, google_oauth_service, test_user):
        """Test Google token exchange."""
        # Mock token response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "ya29.a0Af...",
            "expires_in": 3599,
            "refresh_token": "1//0g...",
            "scope": "https://www.googleapis.com/auth/calendar",
            "token_type": "Bearer"
        }
        mock_post.return_value = mock_response

        # Exchange code for token
        code = "test_auth_code"
        result = await google_oauth_service.exchange_code_for_token(code, test_user)

        # Verify token exchange
        assert result["access_token"] == "test-decrypted-token"
        assert result["refresh_token"] == "test-decrypted-token"
        assert result["expires_in"] == 3599
        assert result["token_type"] == "Bearer"

        # Verify token storage in database
        user = await test_db.users.find_one({"_id": test_user.id})
        assert user["google_access_token"] == "encrypted-token"
        assert user["google_refresh_token"] == "encrypted-token"
        assert "google_token_expiry" in user

    @patch("app.services.google_oauth.requests.post")
    async def test_google_token_exchange_error(self, mock_post, google_oauth_service, test_user):
        """Test Google token exchange error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Attempt token exchange
        code = "invalid_code"
        with pytest.raises(OAuthError) as excinfo:
            await google_oauth_service.exchange_code_for_token(code, test_user)
        
        assert "Invalid authorization code" in str(excinfo.value)

    @patch("app.services.google_oauth.requests.post")
    async def test_google_refresh_token(self, mock_post, google_oauth_service, test_user):
        """Test Google token refresh."""
        # Mock refresh response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "ya29.a0Af...",
            "expires_in": 3599,
            "scope": "https://www.googleapis.com/auth/calendar",
            "token_type": "Bearer"
        }
        mock_post.return_value = mock_response

        # Set expired token
        test_user.google_token_expiry = datetime.utcnow() - timedelta(minutes=5)
        await test_db.users.update_one(
            {"_id": test_user.id},
            {"$set": {"google_token_expiry": test_user.google_token_expiry}}
        )

        # Refresh token
        result = await google_oauth_service.refresh_token(test_user)

        # Verify refresh
        assert result["access_token"] == "test-decrypted-token"
        assert result["expires_in"] == 3599
        assert result["token_type"] == "Bearer"

        # Verify token storage
        user = await test_db.users.find_one({"_id": test_user.id})
        assert user["google_access_token"] == "encrypted-token"
        assert "google_token_expiry" in user

    @patch("app.services.google_oauth.requests.post")
    async def test_google_refresh_token_error(self, mock_post, google_oauth_service, test_user):
        """Test Google token refresh error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Token has been expired or revoked"
        }
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Set expired token
        test_user.google_token_expiry = datetime.utcnow() - timedelta(minutes=5)
        await test_db.users.update_one(
            {"_id": test_user.id},
            {"$set": {"google_token_expiry": test_user.google_token_expiry}}
        )

        # Attempt token refresh
        with pytest.raises(OAuthError) as excinfo:
            await google_oauth_service.refresh_token(test_user)
        
        assert "Token has been expired or revoked" in str(excinfo.value) 