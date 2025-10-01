"""
Test suite for AuthService using proper dependency injection
This replaces the problematic direct instantiation approach with FastAPI's DI system
"""

from datetime import datetime

import pytest

from services.authservice.models import (
    AuthSession,
    UserAlreadyExistsError,
)

# Removed unused import - we instantiate AuthService directly now
from tests.base import ServiceTestBase


class MockUser:
    """Mock User model for testing"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.username = kwargs.get("username", "testuser")
        self.email = kwargs.get("email", "testuser@example.com")
        self.hashed_password = kwargs.get("hashed_password", "fake_hash")
        self.is_superuser = kwargs.get("is_superuser", False)
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at", datetime.now())
        self.last_login = kwargs.get("last_login")


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return MockUser(
        id=1,
        username="testuser",
        email="testuser@example.com",
        hashed_password="fake_hashed_password",
        is_superuser=False,
        is_active=True,
    )


class TestAuthServiceWithDependencyInjection(ServiceTestBase):
    """
    NOTE: These tests duplicate functionality already covered in test_auth_service.py
    They focus on DI mechanics rather than auth behavior and should be consolidated.
    Consider removing these tests as they don't add unique business value.
    """

    @pytest.mark.anyio
    async def test_register_user_success_with_di(self, app):
        """Test successful user registration using dependency injection"""
        # Create fresh mock session for each test to ensure isolation
        mock_session = self.create_mock_session()

        # Configure to return no existing user (allows registration)
        self.configure_mock_query_result(
            mock_session,
            {
                "scalar_one_or_none": None  # No existing user
            },
        )

        # Mock user ID assignment after database operations
        mock_session.refresh.side_effect = lambda user: setattr(user, "id", 1)

        # Create service with mocked session
        from services.authservice.auth_service import AuthService

        service = AuthService(mock_session)

        # Execute the test - this now uses the mocked session
        result = await service.register_user("test_success_user", "ValidPassword123")

        # Verify the result
        assert result is not None

    @pytest.mark.anyio
    async def test_register_user_already_exists_with_di(self, app, mock_user):
        """Test registration fails when user already exists using dependency injection"""
        # Create fresh mock session for each test to ensure isolation
        mock_session = self.create_mock_session()

        # Configure to return existing user (prevents registration)
        self.configure_mock_query_result(
            mock_session,
            {
                "scalar_one_or_none": mock_user  # Existing user found
            },
        )

        # Create service with mocked session
        from services.authservice.auth_service import AuthService

        service = AuthService(mock_session)

        # Execute the test - should raise UserAlreadyExistsError
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await service.register_user("testuser", "ValidPassword123")

        assert "already exists" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_login_success_with_di(self, app, mock_user):
        """Test successful user login using dependency injection"""
        from unittest.mock import patch

        # Create fresh mock session for each test to ensure isolation
        mock_session = self.create_mock_session()

        # Configure to return existing user for login
        self.configure_mock_query_result(
            mock_session,
            {
                "scalar_one_or_none": mock_user  # User found for login
            },
        )

        # Create service with mocked session
        from services.authservice.auth_service import AuthService

        service = AuthService(mock_session)

        # Mock password verification
        with patch.object(service, "_verify_password", return_value=True):
            result = await service.login("testuser", "validpassword")

            # Verify result is AuthSession
            assert isinstance(result, AuthSession)
            assert result.user.username == "testuser"
            assert result.session_token is not None
            assert result.expires_at > datetime.now()
