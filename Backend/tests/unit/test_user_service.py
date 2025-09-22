"""
Unit tests for Auth Service
Following best practices: isolation, mocking, comprehensive coverage
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, UserSession
from services.authservice.auth_service import AuthService
from services.authservice.models import (
    AuthenticationError,
    InvalidCredentialsError,
    SessionExpiredError,
    UserAlreadyExistsError,
)


class TestUserService:
    """Unit tests for UserService class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.fixture
    def user_service(self, mock_session):
        """Create UserService instance with mocked dependencies"""
        return UserService(session=mock_session)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
    
    @pytest.fixture
    def sample_user(self, sample_user_data):
        """Create a sample User object"""
        user = User(
            id=uuid4(),
            username=sample_user_data["username"],
            email=sample_user_data["email"],
            hashed_password="hashed_password",
            first_name=sample_user_data["first_name"],
            last_name=sample_user_data["last_name"],
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow()
        )
        return user
    
    # CREATE Tests
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_session, sample_user_data):
        """Test successful user creation"""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = None  # No existing user
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Act
        user = await user_service.create_user(sample_user_data)
        
        # Assert
        assert user is not None
        assert user.email == sample_user_data["email"]
        assert user.username == sample_user_data["username"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_session, sample_user_data, sample_user):
        """Test user creation with duplicate email"""
        # Arrange
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_user
        
        # Act & Assert
        with pytest.raises(DuplicateUserError) as exc_info:
            await user_service.create_user(sample_user_data)
        
        assert "already exists" in str(exc_info.value)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_service, mock_session):
        """Test user creation with invalid email"""
        # Arrange
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "SecurePassword123!"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(invalid_data)
        
        assert "Invalid email format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, user_service, mock_session):
        """Test user creation with weak password"""
        # Arrange
        weak_password_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_service.create_user(weak_password_data)
        
        assert "Password must be" in str(exc_info.value)
    
    # READ Tests
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_session, sample_user):
        """Test successful user retrieval by ID"""
        # Arrange
        user_id = sample_user.id
        mock_session.get = AsyncMock(return_value=sample_user)
        
        # Act
        user = await user_service.get_user_by_id(user_id)
        
        # Assert
        assert user == sample_user
        mock_session.get.assert_called_once_with(User, user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_session):
        """Test user retrieval with non-existent ID"""
        # Arrange
        user_id = uuid4()
        mock_session.get = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError) as exc_info:
            await user_service.get_user_by_id(user_id)
        
        assert str(user_id) in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_session, sample_user):
        """Test successful user retrieval by email"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=sample_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        user = await user_service.get_user_by_email(sample_user.email)
        
        # Assert
        assert user == sample_user
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_users_with_pagination(self, user_service, mock_session, sample_user):
        """Test retrieving all users with pagination"""
        # Arrange
        users = [sample_user for _ in range(5)]
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=users)))
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_service.get_all_users(skip=0, limit=10)
        
        # Assert
        assert len(result) == 5
        assert result[0] == sample_user
        mock_session.execute.assert_called_once()
    
    # UPDATE Tests
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_session, sample_user):
        """Test successful user update"""
        # Arrange
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        # Act
        updated_user = await user_service.update_user(sample_user.id, update_data)
        
        # Assert
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service, mock_session):
        """Test updating non-existent user"""
        # Arrange
        user_id = uuid4()
        mock_session.get = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await user_service.update_user(user_id, {"first_name": "Updated"})
    
    @pytest.mark.asyncio
    async def test_update_user_email_conflict(self, user_service, mock_session, sample_user):
        """Test updating user with duplicate email"""
        # Arrange
        another_user = User(
            id=uuid4(),
            email="existing@example.com",
            username="existing",
            hashed_password="hash"
        )
        
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=another_user)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act & Assert
        with pytest.raises(DuplicateUserError):
            await user_service.update_user(sample_user.id, {"email": "existing@example.com"})
    
    # DELETE Tests
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_session, sample_user):
        """Test successful user deletion"""
        # Arrange
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_session.delete = AsyncMock()
        mock_session.commit = AsyncMock()
        
        # Act
        result = await user_service.delete_user(sample_user.id)
        
        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_user)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_session):
        """Test deleting non-existent user"""
        # Arrange
        user_id = uuid4()
        mock_session.get = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await user_service.delete_user(user_id)
    
    @pytest.mark.asyncio
    async def test_soft_delete_user(self, user_service, mock_session, sample_user):
        """Test soft deletion (deactivation) of user"""
        # Arrange
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Act
        result = await user_service.soft_delete_user(sample_user.id)
        
        # Assert
        assert result.is_active is False
        assert result.deleted_at is not None
        mock_session.commit.assert_called_once()
    
    # Business Logic Tests
    @pytest.mark.asyncio
    async def test_verify_user_email(self, user_service, mock_session, sample_user):
        """Test email verification process"""
        # Arrange
        sample_user.is_verified = False
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_session.commit = AsyncMock()
        
        # Act
        verified_user = await user_service.verify_email(sample_user.id)
        
        # Assert
        assert verified_user.is_verified is True
        assert verified_user.verified_at is not None
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password(self, user_service, mock_session, sample_user):
        """Test password change functionality"""
        # Arrange
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_session.commit = AsyncMock()
        
        with patch('core.auth.verify_password', return_value=True):
            with patch('core.auth.get_password_hash', return_value="new_hash"):
                # Act
                result = await user_service.change_password(
                    sample_user.id,
                    "old_password",
                    "NewPassword123!"
                )
        
        # Assert
        assert result is True
        assert sample_user.hashed_password == "new_hash"
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, user_service, mock_session, sample_user):
        """Test password change with incorrect current password"""
        # Arrange
        mock_session.get = AsyncMock(return_value=sample_user)
        
        with patch('core.auth.verify_password', return_value=False):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                await user_service.change_password(
                    sample_user.id,
                    "wrong_password",
                    "NewPassword123!"
                )
        
        assert "Current password is incorrect" in str(exc_info.value)
        mock_session.commit.assert_not_called()
    
    # Edge Cases
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, user_service, mock_session, sample_user_data):
        """Test handling of concurrent user creation attempts"""
        # Arrange
        from sqlalchemy.exc import IntegrityError
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_session.add = Mock()
        mock_session.commit = AsyncMock(side_effect=IntegrityError("", "", ""))
        
        # Act & Assert
        with pytest.raises(DuplicateUserError):
            await user_service.create_user(sample_user_data)
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, user_service, mock_session):
        """Test handling of database connection errors"""
        # Arrange
        from sqlalchemy.exc import OperationalError
        
        mock_session.get = AsyncMock(side_effect=OperationalError("", "", ""))
        
        # Act & Assert
        with pytest.raises(OperationalError):
            await user_service.get_user_by_id(uuid4())
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, user_service, mock_session, sample_user):
        """Test transaction rollback on error"""
        # Arrange
        mock_session.get = AsyncMock(return_value=sample_user)
        mock_session.commit = AsyncMock(side_effect=Exception("Database error"))
        mock_session.rollback = AsyncMock()
        
        # Act & Assert
        with pytest.raises(Exception):
            await user_service.update_user(sample_user.id, {"first_name": "Updated"})
        
        mock_session.rollback.assert_called_once()


class TestUserServiceIntegration:
    """Integration tests for UserService with real database"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_user_lifecycle(self, async_session):
        """Test complete user lifecycle: create, read, update, delete"""
        # Arrange
        user_service = UserService(session=async_session)
        user_data = {
            "username": f"testuser_{uuid4().hex[:8]}",
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act - Create
        created_user = await user_service.create_user(user_data)
        assert created_user.id is not None
        user_id = created_user.id
        
        # Act - Read
        retrieved_user = await user_service.get_user_by_id(user_id)
        assert retrieved_user.email == user_data["email"]
        
        # Act - Update
        updated_user = await user_service.update_user(
            user_id,
            {"first_name": "Updated"}
        )
        assert updated_user.first_name == "Updated"
        
        # Act - Delete
        deleted = await user_service.delete_user(user_id)
        assert deleted is True
        
        # Verify deletion
        with pytest.raises(UserNotFoundError):
            await user_service.get_user_by_id(user_id)
