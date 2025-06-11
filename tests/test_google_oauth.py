"""Tests for Google OAuth service."""
import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.google_oauth import GoogleOAuthService
from app.services.encryption import TokenEncryption
from app.core.exceptions import OAuthError
from app.models.mongodb_models import User


# Force skip the autouse setup_test_db fixture
@pytest.fixture(autouse=True)
def skip_setup_test_db():
    """Skip the setup_test_db fixture by patching it."""
    with patch("tests.conftest.setup_test_db", return_value=None):
        yield


@pytest.fixture(autouse=True)
def setup_testing_env():
    """Set testing environment variables"""
    old_env = os.environ.get('TESTING')
    os.environ['TESTING'] = 'true'
    yield
    if old_env is not None:
        os.environ['TESTING'] = old_env
    else:
        del os.environ['TESTING']


@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption


@pytest.fixture
def test_db():
    """Mock MongoDB database."""
    db = MagicMock()
    db.users = AsyncMock()
    db.oauth_states = AsyncMock()
    # Add a list_collections AsyncMock to avoid errors
    db.list_collections = AsyncMock()
    db.list_collections.return_value.__aiter__.return_value = []
    db.drop_collection = AsyncMock()
    return db


@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "_id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "google_access_token": "old-encrypted-token",
        "google_refresh_token": "old-encrypted-refresh-token",
        "google_token_expiry": datetime.utcnow() - timedelta(minutes=5),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def google_oauth_service(mock_token_encryption, test_db):
    """Create a Google OAuth service with mocked dependencies."""
    with patch("app.services.encryption.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.google_oauth.get_settings") as mock_settings:
            mock_settings.return_value.GOOGLE_CLIENT_ID = "test-client-id"
            mock_settings.return_value.GOOGLE_CLIENT_SECRET = "test-client-secret"
            mock_settings.return_value.GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
            mock_settings.return_value.GOOGLE_AUTH_SCOPES = "https://www.googleapis.com/auth/calendar"
            mock_settings.return_value.TOKEN_ENCRYPTION_KEY = "test-encryption-key"
            service = GoogleOAuthService(test_db)
            return service


class TestGoogleOAuthService:
    """Tests for GoogleOAuthService."""

    def test_google_authorization_url(self, google_oauth_service):
        """Test Google authorization URL generation."""
        url, state = google_oauth_service.get_authorization_url()
        
        # Verify URL components
        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http://localhost:8000/auth/google/callback" in url
        assert "scope=https://www.googleapis.com/auth/calendar" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
        assert "state=" in url  # Verify state parameter is present
        assert isinstance(state, str)
        assert len(state) > 10  # State should be reasonably long

    @pytest.mark.asyncio
    @patch("app.services.google_oauth.requests.post")
    async def test_google_token_exchange(self, mock_post, google_oauth_service, test_db, test_user):
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

        # Setup user in database
        test_db.users.find_one.return_value = test_user
        test_db.users.update_one.return_value = AsyncMock(modified_count=1)

        # Exchange code for token
        code = "test_auth_code"
        user_id = "test-user-id"
        result = await google_oauth_service.exchange_code_for_token(code, user_id)

        # Verify token exchange
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["expires_in"] == 3599
        assert result["token_type"] == "Bearer"

        # Verify token storage in database
        test_db.users.update_one.assert_called_once()
        call_args = test_db.users.update_one.call_args[0]
        assert call_args[0] == {"_id": "test-user-id"}
        assert "google_access_token" in call_args[1]["$set"]
        assert "google_refresh_token" in call_args[1]["$set"]
        assert "google_token_expiry" in call_args[1]["$set"]

    @pytest.mark.asyncio
    @patch("app.services.google_oauth.requests.post")
    async def test_google_token_exchange_error(self, mock_post, google_oauth_service, test_db, test_user):
        """Test Google token exchange error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Setup user in database
        test_db.users.find_one.return_value = test_user

        # Attempt token exchange
        code = "invalid_code"
        user_id = "test-user-id"
        with pytest.raises(OAuthError) as excinfo:
            await google_oauth_service.exchange_code_for_token(code, user_id)
        
        assert "Invalid authorization code" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("app.services.google_oauth.requests.post")
    async def test_google_refresh_token(self, mock_post, google_oauth_service, test_db, test_user):
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

        # Setup user in database
        test_db.users.find_one.return_value = test_user
        test_db.users.update_one.return_value = AsyncMock(modified_count=1)

        # Refresh token
        user_id = "test-user-id"
        result = await google_oauth_service.refresh_token(user_id)

        # Verify refresh
        assert "access_token" in result
        assert result["expires_in"] == 3599
        assert result["token_type"] == "Bearer"

        # Verify token storage
        test_db.users.update_one.assert_called_once()
        call_args = test_db.users.update_one.call_args[0]
        assert call_args[0] == {"_id": "test-user-id"}
        assert "google_access_token" in call_args[1]["$set"]
        assert "google_token_expiry" in call_args[1]["$set"]

    @pytest.mark.asyncio
    @patch("app.services.google_oauth.requests.post")
    async def test_google_refresh_token_error(self, mock_post, google_oauth_service, test_db, test_user):
        """Test Google token refresh error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Token has been expired or revoked"
        }
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        # Setup user in database
        test_db.users.find_one.return_value = test_user
        
        # Attempt token refresh
        user_id = "test-user-id"
        with pytest.raises(OAuthError) as excinfo:
            await google_oauth_service.refresh_token(user_id)
        
        assert "Token has been expired or revoked" in str(excinfo.value) 