"""
Test suite for authentication Pydantic models
Tests focus on validation logic that currently has 0% coverage
"""

import pytest
from pydantic import ValidationError

from api.models.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse


class TestRegisterRequestValidation:
    """Test RegisterRequest model validation logic"""

    def test_validate_password_strength_valid_password(self):
        """Test password validation with valid passwords"""
        valid_passwords = ["TestPass123", "SecurePassword1", "MyStr0ngP@ss", "ValidPass123!"]

        for password in valid_passwords:
            request = RegisterRequest(username="testuser", password=password)
            assert request.password == password

    def test_validate_password_strength_missing_uppercase(self):
        """Test password validation fails without uppercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="testuser", password="testpass123")

        error_messages = str(exc_info.value)
        assert "Password must contain at least one uppercase letter" in error_messages

    def test_validate_password_strength_missing_lowercase(self):
        """Test password validation fails without lowercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="testuser", password="TESTPASS123")

        error_messages = str(exc_info.value)
        assert "Password must contain at least one lowercase letter" in error_messages

    def test_validate_password_strength_missing_digit(self):
        """Test password validation fails without digit"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="testuser", password="TestPassword")

        error_messages = str(exc_info.value)
        assert "Password must contain at least one digit" in error_messages

    def test_validate_password_strength_multiple_violations(self):
        """Test password validation with multiple violations"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="testuser", password="weakpass")

        error_messages = str(exc_info.value)
        # Pydantic v2 may only show first validation error, so we check for either
        assert (
            "Password must contain at least one uppercase letter" in error_messages
            or "Password must contain at least one digit" in error_messages
        )

    def test_username_validation_valid(self):
        """Test username validation with valid usernames"""
        valid_usernames = ["testuser", "user123", "my-username", "user_name", "Test-User_123"]

        for username in valid_usernames:
            request = RegisterRequest(username=username, password="ValidPass123")
            assert request.username == username

    def test_username_validation_too_short(self):
        """Test username validation fails when too short"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="ab", password="ValidPass123")

        error_messages = str(exc_info.value)
        assert "String should have at least 3 characters" in error_messages

    def test_username_validation_too_long(self):
        """Test username validation fails when too long"""
        long_username = "a" * 51  # 51 characters
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username=long_username, password="ValidPass123")

        error_messages = str(exc_info.value)
        assert "String should have at most 50 characters" in error_messages

    def test_username_validation_invalid_characters(self):
        """Test username validation fails with invalid characters"""
        invalid_usernames = ["user@domain", "user with spaces", "user.with.dots", "user+special"]

        for username in invalid_usernames:
            with pytest.raises(ValidationError):
                RegisterRequest(username=username, password="ValidPass123")

    def test_password_length_validation(self):
        """Test password length constraints"""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="testuser", password="Short1")

        error_messages = str(exc_info.value)
        assert "String should have at least 8 characters" in error_messages

        # Too long
        long_password = "A" * 129 + "1"  # 130 characters
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(username="testuser", password=long_password)

        error_messages = str(exc_info.value)
        assert "String should have at most 128 characters" in error_messages


class TestLoginRequest:
    """Test LoginRequest model validation"""

    def test_valid_login_request(self):
        """Test valid login request creation"""
        request = LoginRequest(username="testuser", password="anypassword")
        assert request.username == "testuser"
        assert request.password == "anypassword"

    def test_empty_username(self):
        """Test login fails with empty username"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(username="", password="password")

        error_messages = str(exc_info.value)
        assert "String should have at least 1 character" in error_messages

    def test_empty_password(self):
        """Test login fails with empty password"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(username="testuser", password="")

        error_messages = str(exc_info.value)
        assert "String should have at least 1 character" in error_messages


class TestUserResponseModel:
    """Test UserResponse model structure and validation"""

    def test_valid_user_response(self):
        """Test valid UserResponse creation"""
        import random

        user_data = {
            "id": random.randint(1, 1000000),
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": "2024-01-20T14:45:00Z",
        }

        user_response = UserResponse(**user_data)
        assert user_response.username == "testuser"
        assert user_response.email == "test@example.com"
        assert not user_response.is_superuser
        assert user_response.is_active
        assert isinstance(user_response.id, int)

    def test_user_response_with_null_last_login(self):
        """Test UserResponse with null last_login"""
        import random

        user_data = {
            "id": random.randint(1, 1000000),
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": None,
        }

        user_response = UserResponse(**user_data)
        assert user_response.last_login is None
        assert isinstance(user_response.id, int)


class TestAuthResponseModel:
    """Test AuthResponse model structure and validation"""

    def test_valid_auth_response(self):
        """Test valid AuthResponse creation"""
        import random

        user_data = {
            "id": random.randint(1, 1000000),
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": None,
        }

        auth_data = {"token": "jwt_token_here", "user": UserResponse(**user_data), "expires_at": "2024-01-21T14:45:00Z"}

        auth_response = AuthResponse(**auth_data)
        assert auth_response.token == "jwt_token_here"
        assert auth_response.user.username == "testuser"
        assert auth_response.expires_at == "2024-01-21T14:45:00Z"
        assert isinstance(auth_response.user.id, int)

    def test_empty_token_validation(self):
        """Test AuthResponse fails with empty token"""
        import random

        user_data = {
            "id": random.randint(1, 1000000),
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
            "last_login": None,
        }

        with pytest.raises(ValidationError) as exc_info:
            auth_data = {
                "token": "",  # Empty token
                "user": UserResponse(**user_data),
                "expires_at": "2024-01-21T14:45:00Z",
            }
            AuthResponse(**auth_data)

        error_messages = str(exc_info.value)
        assert "String should have at least 1 character" in error_messages


class TestModelEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_register_request_boundary_lengths(self):
        """Test username and password at boundary lengths"""
        # Minimum valid lengths
        request = RegisterRequest(username="abc", password="MinPass1")  # 3 chars, 8 chars
        assert request.username == "abc"
        assert request.password == "MinPass1"

        # Maximum valid lengths
        max_username = "a" * 50
        max_password = "A" * 126 + "a1"  # 128 chars with required patterns
        request = RegisterRequest(username=max_username, password=max_password)
        assert len(request.username) == 50
        assert len(request.password) == 128

    def test_special_characters_in_password(self):
        """Test passwords with special characters are valid"""
        special_passwords = ["Pass123!@#", "SecureP@ss1", "My$tr0ngPa$$", "Test_Pass-123"]

        for password in special_passwords:
            request = RegisterRequest(username="testuser", password=password)
            assert request.password == password
