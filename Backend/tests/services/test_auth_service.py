"""Unit tests for AuthService"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.authservice.auth_service import (
    AuthService, AuthSession, 
    AuthenticationError, InvalidCredentialsError, 
    UserAlreadyExistsError, SessionExpiredError
)
from database.models import User


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def auth_service(mock_db_session):
    """Create AuthService instance with mock database"""
    return AuthService(mock_db_session)


class TestAuthService:
    """Test suite for AuthService"""
    
    def test_init(self, auth_service):
        """Test AuthService initialization"""
        assert auth_service.session_lifetime_hours == 24
        assert auth_service.db_session is not None
        assert auth_service.pwd_context is not None
    
    def test_hash_password(self, auth_service):
        """Test password hashing"""
        password = "test_password"
        hashed = auth_service._hash_password(password)
        assert hashed != password
        assert auth_service._verify_password(password, hashed)
        assert not auth_service._verify_password("wrong_password", hashed)
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_db_session):
        """Test successful user registration"""
        # Mock database response - no existing user found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock refresh to set the user ID after commit
        async def mock_refresh(user):
            user.id = 1
            user.created_at = datetime.now()
        
        mock_db_session.refresh.side_effect = mock_refresh
        
        user = await auth_service.register_user("testuser", "password123")
        
        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.id == 1
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_username(self, auth_service):
        """Test registration with invalid username"""
        with pytest.raises(ValueError, match="Username must be at least 3 characters long"):
            await auth_service.register_user("ab", "password123")
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_password(self, auth_service):
        """Test registration with invalid password"""
        with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
            await auth_service.register_user("testuser", "12345")
    
    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, auth_service, mock_db_session):
        """Test registration when user already exists"""
        # Mock that user already exists
        mock_result = AsyncMock()
        mock_existing_user = Mock()
        mock_existing_user.username = "testuser"
        mock_result.scalar_one_or_none.return_value = mock_existing_user
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register_user("testuser", "password123")
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_db_session):
        """Test successful login"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.hashed_password = auth_service._hash_password("password123")
        mock_user.is_superuser = False
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user.last_login = None
        
        # Mock database response
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        session = await auth_service.login("testuser", "password123")
        
        assert isinstance(session, AuthSession)
        assert session.user.username == "testuser"
        assert len(session.session_token) > 0
        # Verify session was inserted into database
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service, mock_db_session):
        """Test login with invalid credentials"""
        # Mock database response - no user found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("nonexistent", "password123")
    
    @pytest.mark.asyncio
    async def test_validate_session_success(self, auth_service, mock_db_session):
        """Test successful session validation"""
        session_token = "test_token"
        expires_at = datetime.now() + timedelta(hours=1)
        
        # Mock session and user data
        mock_session = Mock()
        mock_session.session_token = session_token
        mock_session.expires_at = expires_at
        mock_session.is_active = True
        mock_session.user_id = 1
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.is_superuser = False
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user.native_language = "en"
        mock_user.target_language = "de"
        mock_user.last_login = None
        
        # Mock database response - result.first() returns tuple (session, user) directly
        mock_result = Mock()
        mock_result.first.return_value = (mock_session, mock_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        user = await auth_service.validate_session(session_token)
        
        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.id == 1
        assert mock_db_session.execute.call_count >= 2  # Initial query + update
    
    @pytest.mark.asyncio
    async def test_validate_session_expired(self, auth_service, mock_db_session):
        """Test validation of expired session"""
        # Mock expired session data
        mock_session = Mock()
        mock_session.session_token = "expired_token"
        mock_session.expires_at = datetime.now() - timedelta(hours=1)  # Expired
        mock_session.is_active = True
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        # Mock database response to return tuple directly
        mock_result = Mock()
        mock_result.first.return_value = (mock_session, mock_user)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(SessionExpiredError):
            await auth_service.validate_session("expired_token")
        
        # Verify session was deactivated in database
        mock_db_session.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_logout(self, auth_service, mock_db_session):
        """Test user logout"""
        session_token = "test_token"
        
        # Mock successful logout (session found and deactivated)
        mock_result = AsyncMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        result = await auth_service.logout(session_token)
        assert result is True
        
        # Test logout with non-existent session
        mock_result.rowcount = 0
        result = await auth_service.logout("nonexistent_token")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_language_preferences(self, auth_service, mock_db_session):
        """Test updating user language preferences"""
        # Language preferences are not yet implemented in the FastAPI-Users model
        # so this method currently returns True as a no-op
        result = await auth_service.update_language_preferences(1, "es", "fr")
        
        assert result is True
        # No database calls expected since this is currently a no-op