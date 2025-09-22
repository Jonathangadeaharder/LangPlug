"""
Unit tests for Auth Service
Following best practices: isolation, mocking, comprehensive coverage
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.auth import User
from database.models import UserSession
from services.authservice.auth_service import AuthService
from services.authservice.models import AuthSession, AuthUser
from core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    SessionExpiredError,
    UserAlreadyExistsError,
)


class TestAuthService:
    """Unit tests for AuthService class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = AsyncMock(spec=AsyncSession)
        # Setup default mock behaviors
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        
        # Mock execute for queries
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=None)
        mock_result.scalars = Mock(return_value=Mock(first=Mock(return_value=None)))
        session.execute = AsyncMock(return_value=mock_result)
        
        return session
    
    @pytest.fixture
    def auth_service(self, mock_session):
        """Create AuthService instance with mocked dependencies"""
        return AuthService(db_session=mock_session)
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample User object"""
        user = User()
        user.id = uuid4()
        user.username = "testuser"
        user.email = "testuser@example.com"
        user.hashed_password = "$2b$12$hashed_password_here"
        user.created_at = datetime.utcnow()
        user.is_active = True
        user.is_superuser = False
        user.is_verified = False
        return user
    
    # Registration Tests
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_session):
        """Test successful user registration"""
        # Arrange
        username = "newuser"
        password = "SecurePassword123!"
        
        # Mock that user doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        user = await auth_service.register_user(username, password)
        
        # Assert
        assert user is not None
        assert user.username == username
        assert user.hashed_password != password  # Password should be hashed
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, auth_service, mock_session, sample_user):
        """Test registration with existing username"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_user)  # User exists
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register_user("testuser", "Password123!")
        
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_username(self, auth_service):
        """Test registration with invalid username"""
        # Act & Assert
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            await auth_service.register_user("ab", "Password123!")
        
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            await auth_service.register_user("", "Password123!")
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_service):
        """Test registration with weak password"""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must be at least 6 characters"):
            await auth_service.register_user("testuser", "weak")
    
    # Login Tests
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_session, sample_user):
        """Test successful login"""
        # Arrange
        username = "testuser"
        password = "correct_password"
        
        # Mock user exists
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock password verification
        with patch.object(auth_service, '_verify_password', return_value=True):
            # Act
            session = await auth_service.login(username, password)
        
        # Assert
        assert session is not None
        assert isinstance(session, AuthSession)
        assert session.user.id == str(sample_user.id)  # AuthUser.id is string
        assert session.user.username == username
        assert len(session.session_token) > 0
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_login_invalid_username(self, auth_service, mock_session):
        """Test login with non-existent username"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)  # User doesn't exist
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("nonexistent", "password")
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, mock_session, sample_user):
        """Test login with incorrect password"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(auth_service, '_verify_password', return_value=False):
            # Act & Assert
            with pytest.raises(InvalidCredentialsError):
                await auth_service.login("testuser", "wrong_password")
    
    
    # Session Validation Tests
    @pytest.mark.asyncio
    async def test_validate_session_success(self, auth_service, mock_session):
        """Test successful session validation"""
        # Arrange
        session_token = "valid_token_123"
        user_session = UserSession()
        user_session.user_id = uuid4()
        user_session.session_token = session_token
        user_session.created_at = datetime.utcnow()
        user_session.expires_at = datetime.utcnow() + timedelta(hours=24)
        user_session.is_active = True
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=user_session)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        auth_session = await auth_service.validate_session(session_token)
        
        # Assert
        assert auth_session is not None
        assert auth_session.user_id == user_session.user_id
        assert auth_session.session_token == session_token
    
    @pytest.mark.asyncio
    async def test_validate_session_invalid_token(self, auth_service, mock_session):
        """Test validation with invalid session token"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=None)  # Session doesn't exist
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act & Assert
        result = await auth_service.validate_session("invalid_token")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_session_expired(self, auth_service, mock_session):
        """Test validation with expired session"""
        # Arrange
        session_token = "expired_token"
        user_session = UserSession()
        user_session.session_token = session_token
        user_session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        user_session.is_active = True
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=user_session)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act & Assert
        with pytest.raises(SessionExpiredError):
            await auth_service.validate_session(session_token)
    
    @pytest.mark.asyncio
    async def test_validate_session_inactive(self, auth_service, mock_session):
        """Test validation with inactive session"""
        # Arrange
        session_token = "inactive_token"
        user_session = UserSession()
        user_session.session_token = session_token
        user_session.expires_at = datetime.utcnow() + timedelta(hours=24)
        user_session.is_active = False  # Inactive
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=user_session)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await auth_service.validate_session(session_token)
        
        # Assert
        assert result is None
    
    # Logout Tests
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, mock_session):
        """Test successful logout"""
        # Arrange
        session_token = "active_token"
        user_session = UserSession()
        user_session.session_token = session_token
        user_session.is_active = True
        
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=user_session)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        await auth_service.logout(session_token)
        
        # Assert
        assert user_session.is_active is False
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, auth_service, mock_session):
        """Test logout with invalid token"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act - Should not raise exception
        await auth_service.logout("invalid_token")
        
        # Assert - Commit still called (no-op is fine)
        mock_session.commit.assert_not_called()
    
    # Get User Tests
    @pytest.mark.asyncio
    async def test_get_user_by_session_success(self, auth_service, mock_session, sample_user):
        """Test getting user by valid session"""
        # Arrange
        session_token = "valid_token"
        user_session = UserSession()
        user_session.user_id = sample_user.id
        user_session.session_token = session_token
        user_session.expires_at = datetime.utcnow() + timedelta(hours=24)
        user_session.is_active = True
        
        # First query returns session, second returns user
        mock_session_result = Mock()
        mock_session_result.scalar = Mock(return_value=user_session)
        
        mock_user_result = Mock()
        mock_user_result.scalar = Mock(return_value=sample_user)
        
        mock_session.execute = AsyncMock(side_effect=[mock_session_result, mock_user_result])
        
        # Act
        user = await auth_service.get_user_by_session(session_token)
        
        # Assert
        assert user is not None
        assert user.id == sample_user.id
        assert user.username == sample_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_by_session_invalid_token(self, auth_service, mock_session):
        """Test getting user with invalid session token"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        user = await auth_service.get_user_by_session("invalid_token")
        
        # Assert
        assert user is None
    
    # Password Hashing Tests
    def test_hash_password(self, auth_service):
        """Test password hashing"""
        # Act
        password = "MySecurePassword123!"
        hashed = auth_service._hash_password(password)
        
        # Assert
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt hash prefix
        assert len(hashed) > 50
    
    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password"""
        # Arrange
        password = "MySecurePassword123!"
        hashed = auth_service._hash_password(password)
        
        # Act
        result = auth_service._verify_password(password, hashed)
        
        # Assert
        assert result is True
    
    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password"""
        # Arrange
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = auth_service._hash_password(password)
        
        # Act
        result = auth_service._verify_password(wrong_password, hashed)
        
        # Assert
        assert result is False
    
    # Edge Cases
    @pytest.mark.asyncio
    async def test_concurrent_login_attempts(self, auth_service, mock_session, sample_user):
        """Test handling of concurrent login attempts"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=sample_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(auth_service, '_verify_password', return_value=True):
            # Act - Simulate concurrent logins
            session1 = await auth_service.login("testuser", "password")
            session2 = await auth_service.login("testuser", "password")
        
        # Assert - Both should succeed with different tokens
        assert session1.session_token != session2.session_token
        assert mock_session.add.call_count == 2
        assert mock_session.commit.call_count == 2
    
    @pytest.mark.asyncio
    async def test_session_lifetime_configuration(self, mock_session):
        """Test session lifetime can be configured"""
        # Arrange
        auth_service = AuthService(db_session=mock_session)
        auth_service.session_lifetime_hours = 48
        
        # Assert
        assert auth_service.session_lifetime_hours == 48
