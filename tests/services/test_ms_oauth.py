"""
Tests for Microsoft OAuth service.
"""
import datetime
import os
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from fastapi import HTTPException

from app.models.mongodb_models import User
from app.services.ms_oauth import MicrosoftOAuthService
from app.services.encryption import TokenEncryption
from app.core.exceptions import OAuthError


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
def mock_oauth_states():
    """Mock for the oauth_states dictionary"""
    with patch('app.services.oauth_service.oauth_states', {}) as mock_states:
        yield mock_states


@pytest.fixture
def mock_db():
    """Mock MongoDB database."""
    db = MagicMock()
    db.users = AsyncMock()
    db.oauth_states = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Mock user with Microsoft credentials."""
    return {
        "_id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "microsoft_access_token": "encrypted-access-token",
        "microsoft_refresh_token": "encrypted-refresh-token",
        "microsoft_token_expiry": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }


@pytest.fixture
def mock_token_encryption():
    """Mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "decrypted-token"
    return encryption


@pytest.fixture
def ms_oauth_service(mock_db, mock_token_encryption):
    """Create a Microsoft OAuth service with mocked dependencies."""
    with patch("app.services.ms_oauth.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.ms_oauth.get_settings") as mock_settings:
            mock_settings.return_value.MS_CLIENT_ID = "test-client-id"
            mock_settings.return_value.MS_CLIENT_SECRET = "test-client-secret"
            mock_settings.return_value.MS_TENANT_ID = "test-tenant-id"
            mock_settings.return_value.MS_REDIRECT_URI = "http://localhost:8000/auth/ms/callback"
            mock_settings.return_value.MS_AUTH_SCOPES = "openid profile offline_access User.Read Calendars.ReadWrite"
            mock_settings.return_value.TOKEN_ENCRYPTION_KEY = "test-encryption-key"
            service = MicrosoftOAuthService(mock_db)
            return service


class TestMicrosoftOAuthService:
    """Tests for MicrosoftOAuthService."""

    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    def test_generate_auth_url(self, mock_msal_app, ms_oauth_service):
        """Test generating authorization URL."""
        # Setup
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.get_authorization_request_url.return_value = "https://login.microsoftonline.com/test_tenant_id/oauth2/v2.0/authorize?client_id=test-client-id&response_type=code"
        
        # Test
        auth_url, state = ms_oauth_service.get_authorization_url()
        
        # Verify
        assert "https://login.microsoftonline.com/" in auth_url
        assert isinstance(state, str)
        assert len(state) > 10  # State should be a reasonably long string

    @pytest.mark.asyncio
    async def test_save_state(self, ms_oauth_service, mock_db, mock_oauth_states):
        """Test saving state to database."""
        # Setup
        state = "test-state"
        user_id = "test-user-id"

        # Test
        await ms_oauth_service.save_state(state, user_id)

        # Verify - in test mode, should save to oauth_states dict, not call DB
        assert state in mock_oauth_states
        assert mock_oauth_states[state]["user_id"] == user_id
        # Make sure DB wasn't called since we're in test mode
        mock_db.oauth_states.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_state_valid(self, ms_oauth_service, mock_db, mock_oauth_states):
        """Test validating a valid state."""
        # Setup
        state = "test-state"
        user_id = "test-user-id"
        mock_oauth_states[state] = {
            "user_id": user_id,
            "expires": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }

        # Test
        result = await ms_oauth_service.validate_state(state)

        # Verify
        assert result == user_id
        assert state not in mock_oauth_states  # State should be removed after validation
        # Make sure DB wasn't called since we're in test mode
        mock_db.oauth_states.find_one.assert_not_called()
        mock_db.oauth_states.delete_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_state_invalid(self, ms_oauth_service, mock_db, mock_oauth_states):
        """Test validating an invalid state."""
        # Test with pytest.raises
        with pytest.raises(OAuthError) as exc_info:
            await ms_oauth_service.validate_state("invalid-state")

        # Verify error message contains expected text
        assert "Invalid OAuth state" == str(exc_info.value)
        mock_db.oauth_states.find_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_state_expired(self, ms_oauth_service, mock_db, mock_oauth_states):
        """Test validating an expired state."""
        # Setup
        state = "expired-state"
        user_id = "test-user-id"
        mock_oauth_states[state] = {
            "user_id": user_id,
            "expires": datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        }

        # Test with pytest.raises
        with pytest.raises(OAuthError) as exc_info:
            await ms_oauth_service.validate_state(state)

        # Verify error message contains expected text
        assert "OAuth state expired" == str(exc_info.value)
        assert state not in mock_oauth_states  # State should be removed even if expired
        mock_db.oauth_states.find_one.assert_not_called()
        mock_db.oauth_states.delete_one.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    async def test_get_token(self, mock_msal_app, ms_oauth_service, mock_db, mock_user):
        """Test getting token successfully."""
        # Setup
        mock_db.users.find_one.return_value = mock_user
        mock_db.users.update_one.return_value = AsyncMock(modified_count=1)
        
        # Mock the exchange_code_for_token method
        with patch.object(ms_oauth_service, 'exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
                "id_token_claims": {"preferred_username": "test@example.com", "oid": "ms-user-id"}
            }

            # Test
            result = await ms_oauth_service.get_token("test-code", "test-user-id")

            # Verify
            mock_exchange.assert_called_once_with("test-code")
            mock_db.users.update_one.assert_called_once()
            assert "access_token" in result

    @pytest.mark.asyncio
    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    async def test_get_token_error(self, mock_msal_app, ms_oauth_service, mock_db, mock_user):
        """Test getting token with error."""
        # Setup
        mock_db.users.find_one.return_value = mock_user
        
        # Mock the exchange_code_for_token method to raise an exception
        with patch.object(ms_oauth_service, 'exchange_code_for_token') as mock_exchange:
            mock_exchange.side_effect = Exception("Invalid grant: AADSTS70000: Invalid authorization code")

            # Test
            with pytest.raises(OAuthError) as exc_info:
                await ms_oauth_service.get_token("test-code", "test-user-id")

            # Verify
            mock_exchange.assert_called_once_with("test-code")
            assert "token" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_token_user_not_found(self, ms_oauth_service, mock_db):
        """Test getting token when user not found."""
        # Setup
        mock_db.users.find_one.return_value = None

        # Test
        with pytest.raises(OAuthError) as exc_info:
            await ms_oauth_service.get_token("test-code", "non-existent-user")

        # Verify - Now we only check that an OAuthError was raised
        assert isinstance(exc_info.value, OAuthError)
