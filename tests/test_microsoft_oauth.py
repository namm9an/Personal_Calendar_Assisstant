"""Tests for Microsoft OAuth service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from app.services.ms_oauth import MicrosoftOAuthService
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
def microsoft_oauth_service(mock_token_encryption, test_db):
    """Create a Microsoft OAuth service with mocked dependencies."""
    with patch("app.services.ms_oauth.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.ms_oauth.settings") as mock_settings:
            mock_settings.MS_CLIENT_ID = "test-client-id"
            mock_settings.MS_CLIENT_SECRET = "test-client-secret"
            mock_settings.MS_REDIRECT_URI = "http://localhost:8000/auth/microsoft/callback"
            mock_settings.MS_AUTH_SCOPES = "https://graph.microsoft.com/Calendars.ReadWrite"
            mock_settings.TOKEN_ENCRYPTION_KEY = "test-encryption-key"
            service = MicrosoftOAuthService(test_db)
            return service

class TestMicrosoftOAuthService:
    """Tests for MicrosoftOAuthService."""

    def test_get_authorization_url(self, microsoft_oauth_service):
        """Test Microsoft authorization URL generation."""
        url, state = microsoft_oauth_service.get_authorization_url()
        
        # Verify URL components
        assert "https://login.microsoftonline.com/test_tenant_id/oauth2/v2.0/authorize" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http://localhost:8000/auth/microsoft/callback" in url
        assert "scope=https://graph.microsoft.com/Calendars.ReadWrite" in url
        assert "response_type=code" in url
        assert "response_mode=query" in url
        assert state is not None  # Verify state parameter is present

    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    def test_exchange_code_for_token(self, mock_msal_app, microsoft_oauth_service):
        """Test Microsoft token exchange."""
        # Mock token response
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_authorization_code.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3599,
            "token_type": "Bearer",
            "id_token_claims": {
                "oid": "test-user-oid",
                "preferred_username": "test@example.com"
            }
        }

        # Exchange code for token
        code = "test_auth_code"
        result = microsoft_oauth_service.exchange_code_for_token(code)

        # Verify token exchange
        assert result["access_token"] == "test-access-token"
        assert result["refresh_token"] == "test-refresh-token"
        assert result["expires_in"] == 3599
        assert result["token_type"] == "Bearer"
        assert result["id_token_claims"]["oid"] == "test-user-oid"

    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    def test_exchange_code_for_token_error(self, mock_msal_app, microsoft_oauth_service):
        """Test Microsoft token exchange error handling."""
        # Mock error response
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_authorization_code.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }

        # Attempt token exchange
        with pytest.raises(OAuthError) as excinfo:
            microsoft_oauth_service.exchange_code_for_token("invalid_code")
        
        assert "Invalid authorization code" in str(excinfo.value)

    def test_save_user_tokens(self, microsoft_oauth_service, test_user):
        """Test saving Microsoft tokens for a user."""
        # Token data
        token_data = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3599,
            "id_token_claims": {
                "oid": "test-user-oid"
            }
        }

        # Save tokens
        user = microsoft_oauth_service.save_user_tokens(str(test_user.id), token_data)

        # Verify token storage
        assert user.microsoft_access_token == "encrypted-token"
        assert user.microsoft_refresh_token == "encrypted-token"
        assert user.microsoft_id == "test-user-oid"
        assert user.microsoft_token_expiry is not None

    def test_save_user_tokens_invalid_data(self, microsoft_oauth_service, test_user):
        """Test saving invalid token data."""
        # Invalid token data
        token_data = {
            "expires_in": 3599
        }

        # Attempt to save tokens
        with pytest.raises(OAuthError) as excinfo:
            microsoft_oauth_service.save_user_tokens(str(test_user.id), token_data)
        
        assert "Invalid token data" in str(excinfo.value)

    def test_get_tokens(self, microsoft_oauth_service, test_user):
        """Test getting Microsoft tokens for a user."""
        # Set up test user with tokens
        test_user.microsoft_access_token = "encrypted-token"
        test_user.microsoft_refresh_token = "encrypted-token"
        test_user.microsoft_token_expiry = datetime.utcnow() + timedelta(hours=1)

        # Get tokens
        access_token, refresh_token, expiry = microsoft_oauth_service.get_tokens(str(test_user.id))

        # Verify tokens
        assert access_token == "test-decrypted-token"
        assert refresh_token == "test-decrypted-token"
        assert expiry == test_user.microsoft_token_expiry

    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    def test_get_tokens_refresh(self, mock_msal_app, microsoft_oauth_service, test_user):
        """Test token refresh when getting tokens."""
        # Set up test user with expired tokens
        test_user.microsoft_access_token = "encrypted-token"
        test_user.microsoft_refresh_token = "encrypted-token"
        test_user.microsoft_token_expiry = datetime.utcnow() - timedelta(minutes=5)

        # Mock refresh response
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_refresh_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3599
        }

        # Get tokens
        access_token, refresh_token, expiry = microsoft_oauth_service.get_tokens(str(test_user.id))

        # Verify refreshed tokens
        assert access_token == "new-access-token"
        assert refresh_token == "new-refresh-token"
        assert expiry > datetime.utcnow()

    def test_save_state(self, microsoft_oauth_service):
        """Test saving OAuth state."""
        state = "test-state"
        user_id = "test-user-id"

        # Save state
        microsoft_oauth_service.save_state(state, user_id)

        # Verify state was saved
        assert state in microsoft_oauth_service._test_states
        assert microsoft_oauth_service._test_states[state] == user_id

    def test_validate_state(self, microsoft_oauth_service):
        """Test validating OAuth state."""
        state = "test-state"
        user_id = "test-user-id"

        # Save state
        microsoft_oauth_service.save_state(state, user_id)

        # Validate state
        result = microsoft_oauth_service.validate_state(state)

        # Verify state was validated and removed
        assert result == user_id
        assert state not in microsoft_oauth_service._test_states

    def test_validate_state_invalid(self, microsoft_oauth_service):
        """Test validating invalid OAuth state."""
        with pytest.raises(OAuthError) as excinfo:
            microsoft_oauth_service.validate_state("invalid-state")
        
        assert "Invalid state parameter" in str(excinfo.value)

    def test_get_token(self, microsoft_oauth_service, test_user):
        """Test getting token for a user."""
        # Mock token exchange
        with patch.object(microsoft_oauth_service, 'exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3599
            }

            # Get token
            result = microsoft_oauth_service.get_token("test-code", str(test_user.id))

            # Verify token exchange and storage
            assert result["access_token"] == "test-access-token"
            assert result["refresh_token"] == "test-refresh-token"
            assert result["expires_in"] == 3599
            mock_exchange.assert_called_once_with("test-code") 