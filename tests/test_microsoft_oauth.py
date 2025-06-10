"""Tests for Microsoft OAuth service."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from bson import ObjectId
from app.services.ms_oauth import MicrosoftOAuthService
from app.services.encryption import TokenEncryption
from app.core.exceptions import OAuthError
from app.models.mongodb_models import User

@pytest.fixture
def mock_token_encryption():
    """Create a mock token encryption service."""
    encryption = MagicMock(spec=TokenEncryption)
    encryption.encrypt.return_value = "encrypted-token"
    encryption.decrypt.return_value = "test-decrypted-token"
    return encryption

@pytest_asyncio.fixture
async def microsoft_oauth_service(mock_token_encryption, test_db):
    """Create a Microsoft OAuth service with mocked dependencies."""
    with patch("app.services.ms_oauth.TokenEncryption", return_value=mock_token_encryption):
        with patch("app.services.ms_oauth.settings") as mock_settings:
            mock_settings.MS_CLIENT_ID = "test-client-id"
            mock_settings.MS_CLIENT_SECRET = "test-client-secret"
            mock_settings.MS_REDIRECT_URI = "http://localhost:8000/auth/microsoft/callback"
            mock_settings.MS_AUTH_SCOPES = "https://graph.microsoft.com/Calendars.ReadWrite"
            mock_settings.TOKEN_ENCRYPTION_KEY = "test-encryption-key"
            mock_settings.MS_TENANT_ID = "254fcc38-6701-49ea-8072-be2d7f178ae3"  # Real tenant ID
            service = MicrosoftOAuthService(test_db)
            # Create a test OAuth states collection
            await test_db.create_collection("oauth_states")
            yield service
            # Clean up
            await test_db.drop_collection("oauth_states")

@pytest_asyncio.fixture
async def test_mongodb_user(test_db):
    """Create a test user in MongoDB."""
    user_id = str(ObjectId())
    user_data = {
        "_id": user_id,
        "email": "test@example.com",
        "name": "Test User",
        "timezone": "UTC",
        "working_hours_start": "09:00",
        "working_hours_end": "17:00",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "preferences": {},
        "microsoft_access_token": "encrypted-token",
        "microsoft_refresh_token": "encrypted-token",
        "microsoft_token_expiry": datetime.utcnow() + timedelta(hours=1)
    }
    
    await test_db.users.insert_one(user_data)
    user = User(**user_data)
    yield user
    # Clean up
    await test_db.users.delete_one({"_id": user_id})

class TestMicrosoftOAuthService:
    """Tests for MicrosoftOAuthService."""

    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    def test_get_authorization_url(self, mock_msal_app, microsoft_oauth_service):
        """Test Microsoft authorization URL generation."""
        # Mock the get_authorization_request_url method
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.get_authorization_request_url.return_value = (
            "https://login.microsoftonline.com/254fcc38-6701-49ea-8072-be2d7f178ae3/oauth2/v2.0/authorize"
            "?client_id=test-client-id"
            "&response_type=code"
            "&redirect_uri=http://localhost:8000/auth/microsoft/callback"
            "&scope=https://graph.microsoft.com/Calendars.ReadWrite"
            "&state=test-state"
        )
        
        url, state = microsoft_oauth_service.get_authorization_url()
        
        # Verify URL components
        assert "https://login.microsoftonline.com/254fcc38-6701-49ea-8072-be2d7f178ae3/oauth2/v2.0/authorize" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http://localhost:8000/auth/microsoft/callback" in url
        assert "scope=https://graph.microsoft.com/Calendars.ReadWrite" in url
        assert "response_type=code" in url
        assert "state=" in url
        assert state is not None  # Verify state parameter is present
        
        # Verify the mock was called with correct parameters
        mock_app_instance.get_authorization_request_url.assert_called_once()
        call_args = mock_app_instance.get_authorization_request_url.call_args[1]
        assert call_args["scopes"] == ["https://graph.microsoft.com/Calendars.ReadWrite"]
        assert call_args["redirect_uri"] == "http://localhost:8000/auth/microsoft/callback"
        assert "state" in call_args

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

    @pytest.mark.asyncio
    async def test_save_user_tokens(self, microsoft_oauth_service, test_mongodb_user):
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
        user = await microsoft_oauth_service.save_user_tokens(test_mongodb_user.id, token_data)

        # Verify token storage
        assert user.microsoft_access_token == "encrypted-token"
        assert user.microsoft_refresh_token == "encrypted-token"
        assert user.microsoft_id == "test-user-oid"
        assert user.microsoft_token_expiry is not None

    @pytest.mark.asyncio
    async def test_save_user_tokens_invalid_data(self, microsoft_oauth_service, test_mongodb_user):
        """Test saving invalid token data."""
        # Invalid token data
        token_data = {
            "expires_in": 3599
        }

        # Attempt to save tokens
        with pytest.raises(OAuthError) as excinfo:
            await microsoft_oauth_service.save_user_tokens(test_mongodb_user.id, token_data)
        
        assert "Invalid token data" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_tokens(self, microsoft_oauth_service, test_mongodb_user):
        """Test getting Microsoft tokens for a user."""
        # Get tokens
        access_token, refresh_token, expiry = await microsoft_oauth_service.get_tokens(test_mongodb_user.id)

        # Verify tokens
        assert access_token == "test-decrypted-token"
        assert refresh_token == "test-decrypted-token"
        assert isinstance(expiry, datetime)

    @patch("app.services.ms_oauth.msal.ConfidentialClientApplication")
    @pytest.mark.asyncio
    async def test_get_tokens_refresh(self, mock_msal_app, microsoft_oauth_service, test_db):
        """Test token refresh when getting tokens."""
        # Create a user with expired tokens
        user_id = str(ObjectId())
        user_data = {
            "_id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "timezone": "UTC",
            "working_hours_start": "09:00",
            "working_hours_end": "17:00",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "preferences": {},
            "microsoft_access_token": "encrypted-token",
            "microsoft_refresh_token": "encrypted-token",
            "microsoft_token_expiry": datetime.utcnow() - timedelta(minutes=5)
        }
        
        await test_db.users.insert_one(user_data)

        # Mock refresh response
        mock_app_instance = mock_msal_app.return_value
        mock_app_instance.acquire_token_by_refresh_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3599
        }

        # Get tokens
        access_token, refresh_token, expiry = await microsoft_oauth_service.get_tokens(user_id)

        # Verify refreshed tokens
        assert access_token == "new-access-token"
        assert refresh_token == "new-refresh-token"
        assert expiry > datetime.utcnow()
        
        # Clean up
        await test_db.users.delete_one({"_id": user_id})

    @pytest.mark.asyncio
    async def test_save_state(self, microsoft_oauth_service):
        """Test saving OAuth state."""
        state = "test-state"
        user_id = "test-user-id"

        # Save state
        await microsoft_oauth_service.save_state(state, user_id)

        # For testing mode, verify state was saved in memory
        from app.services.oauth_service import oauth_states
        assert state in oauth_states
        assert oauth_states[state]["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_validate_state(self, microsoft_oauth_service):
        """Test validating OAuth state."""
        state = "test-state"
        user_id = "test-user-id"

        # Save state
        await microsoft_oauth_service.save_state(state, user_id)

        # Validate state
        result = await microsoft_oauth_service.validate_state(state)

        # Verify state was validated and removed
        assert result == user_id
        from app.services.oauth_service import oauth_states
        assert state not in oauth_states

    @pytest.mark.asyncio
    async def test_validate_state_invalid(self, microsoft_oauth_service):
        """Test validating invalid OAuth state."""
        with pytest.raises(OAuthError) as excinfo:
            await microsoft_oauth_service.validate_state("invalid-state")
        
        assert "Invalid OAuth state" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_token(self, microsoft_oauth_service, test_mongodb_user):
        """Test getting token for a user."""
        # Mock token exchange
        with patch.object(microsoft_oauth_service, 'exchange_code_for_token') as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3599
            }

            # Get token
            result = await microsoft_oauth_service.get_token("test-code", test_mongodb_user.id)

            # Verify token exchange and storage
            assert result["access_token"] == "test-access-token"
            assert result["refresh_token"] == "test-refresh-token"
            assert result["expires_in"] == 3599
            mock_exchange.assert_called_once_with("test-code") 