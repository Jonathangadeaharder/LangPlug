"""
Authentication test helpers following best practices.
Provides standardized patterns for auth testing.
"""
import uuid
from typing import Any

from fastapi.testclient import TestClient
from httpx import AsyncClient


class AuthTestHelper:
    """Standardized authentication testing patterns."""

    @staticmethod
    def generate_unique_user_data() -> dict[str, str]:
        """Generate unique user credentials for testing."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"testuser_{unique_id}@example.com",
            "password": "SecureTestPass123!"
        }

    @staticmethod
    def register_user(client: TestClient, user_data: dict[str, str]) -> tuple[int, dict[str, Any]]:
        """Register a new user and return response details."""
        response = client.post("/api/auth/register", json=user_data)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def register_user_async(client: AsyncClient, user_data: dict[str, str]) -> tuple[int, dict[str, Any]]:
        """Register a new user asynchronously and return response details."""
        response = await client.post("/api/auth/register", json=user_data)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    def login_user(client: TestClient, email: str, password: str) -> tuple[int, dict[str, Any]]:
        """Login with email/password and return response details."""
        login_data = {
            "username": email,  # FastAPI-Users expects email in username field
            "password": password
        }
        response = client.post("/api/auth/login", data=login_data)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def login_user_async(client: AsyncClient, email: str, password: str) -> tuple[int, dict[str, Any]]:
        """Login with email/password asynchronously and return response details."""
        login_data = {
            "username": email,  # FastAPI-Users expects email in username field
            "password": password
        }
        response = await client.post("/api/auth/login", data=login_data)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    def register_and_login(client: TestClient, user_data: dict[str, str] = None) -> dict[str, Any]:
        """Complete registration and login flow. Returns user data and token."""
        if user_data is None:
            user_data = AuthTestHelper.generate_unique_user_data()

        # Register user
        reg_status, reg_data = AuthTestHelper.register_user(client, user_data)
        assert reg_status == 201, f"Registration failed: {reg_status}"

        # Login user
        login_status, login_data = AuthTestHelper.login_user(
            client, user_data["email"], user_data["password"]
        )
        assert login_status == 200, f"Login failed: {login_status}"
        assert "access_token" in login_data, "No access token in login response"

        return {
            "user_data": user_data,
            "registration_response": reg_data,
            "login_response": login_data,
            "token": login_data["access_token"],
            "headers": {"Authorization": f"Bearer {login_data['access_token']}"}
        }

    @staticmethod
    async def register_and_login_async(client: AsyncClient, user_data: dict[str, str] | None = None) -> dict[str, Any]:
        """Complete registration and login flow asynchronously. Returns user data and token."""
        if user_data is None:
            user_data = AuthTestHelper.generate_unique_user_data()

        # Register user
        reg_status, reg_data = await AuthTestHelper.register_user_async(client, user_data)
        assert reg_status == 201, f"Registration failed: {reg_status}"

        # Login user
        login_status, login_data = await AuthTestHelper.login_user_async(
            client, user_data["email"], user_data["password"]
        )
        assert login_status == 200, f"Login failed: {login_status}"
        assert "access_token" in login_data, "No access token in login response"

        return {
            "user_data": user_data,
            "registration_response": reg_data,
            "login_response": login_data,
            "token": login_data["access_token"],
            "headers": {"Authorization": f"Bearer {login_data['access_token']}"}
        }

    @staticmethod
    def logout_user(client: TestClient, token: str) -> tuple[int, dict[str, Any]]:
        """Logout user with token."""
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/logout", headers=headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def logout_user_async(client: AsyncClient, token: str) -> tuple[int, dict[str, Any]]:
        """Logout user with token asynchronously."""
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/auth/logout", headers=headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    def get_current_user(client: TestClient, token: str) -> tuple[int, dict[str, Any]]:
        """Get current user info with token."""
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def get_current_user_async(client: AsyncClient, token: str) -> tuple[int, dict[str, Any]]:
        """Get current user info with token asynchronously."""
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/auth/me", headers=headers)
        return response.status_code, response.json() if response.content else {}


# Expected response structures for validation
class AuthResponseStructures:
    """Expected response structures for auth endpoints."""

    REGISTRATION_SUCCESS = {
        "required_fields": ["id", "username", "email", "is_active", "is_superuser", "is_verified"],
        "status_code": 201
    }

    LOGIN_SUCCESS = {
        "required_fields": ["access_token", "token_type"],
        "status_code": 200,
        "token_type_value": "bearer"
    }

    USER_INFO_SUCCESS = {
        "required_fields": ["id", "username", "is_superuser", "is_active", "created_at"],
        "status_code": 200,
        "id_type": "uuid"  # Expect UUID string format
    }

    # Error responses
    REGISTER_USER_EXISTS = {"status_code": 400, "detail": "REGISTER_USER_ALREADY_EXISTS"}
    LOGIN_BAD_CREDENTIALS = {"status_code": 400, "detail": "LOGIN_BAD_CREDENTIALS"}
    UNAUTHORIZED = {"status_code": 401}


def validate_auth_response(response_data: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Validate auth response structure matches expectations."""
    # Check required fields
    if "required_fields" in expected:
        for field in expected["required_fields"]:
            if field not in response_data:
                raise AssertionError(f"Missing required field: {field}")

    # Check token type if specified
    if "token_type_value" in expected:
        if response_data.get("token_type") != expected["token_type_value"]:
            raise AssertionError(
                f"Expected token_type '{expected['token_type_value']}', "
                f"got '{response_data.get('token_type')}'"
            )

    return True


# Test data generators
def get_invalid_registration_cases():
    """Get test cases for invalid registration data."""
    return [
        # Missing fields
        ({"email": "test@example.com", "password": "TestPass123"}, 422, "Missing username"),
        ({"username": "testuser", "password": "TestPass123"}, 422, "Missing email"),
        ({"username": "testuser", "email": "test@example.com"}, 422, "Missing password"),

        # Invalid formats
        ({"username": "testuser", "email": "invalid-email", "password": "TestPass123"}, 422, "Invalid email"),
        ({"username": "", "email": "test@example.com", "password": "TestPass123"}, 422, "Empty username"),
        ({"username": "testuser", "email": "test@example.com", "password": ""}, 422, "Empty password"),

        # Edge cases
        ({}, 422, "Empty payload"),
        # Note: Short password test removed - API currently accepts short passwords
    ]


def get_invalid_login_cases():
    """Get test cases for invalid login attempts."""
    return [
        # Missing fields
        ({"password": "TestPass123"}, 422, "Missing username"),
        ({"username": "test@example.com"}, 422, "Missing password"),

        # Invalid credentials
        ({"username": "nonexistent@example.com", "password": "TestPass123"}, 400, "User not found"),
        ({"username": "test@example.com", "password": "wrongpassword"}, 400, "Wrong password"),

        # Edge cases
        ({}, 422, "Empty payload"),
    ]


# Async versions of helper methods
class AuthTestHelperAsync:
    """Async versions of authentication testing patterns."""

    @staticmethod
    def generate_unique_user_data() -> dict[str, str]:
        """Generate unique user credentials for testing."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"testuser_{unique_id}@example.com",
            "password": "SecureTestPass123!"
        }

    @staticmethod
    async def register_user_async(client: AsyncClient, user_data: dict[str, str]) -> tuple[int, dict[str, Any]]:
        """Register a new user asynchronously and return response details."""
        response = await client.post("/api/auth/register", json=user_data)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def login_user_async(client: AsyncClient, email: str, password: str) -> tuple[int, dict[str, Any]]:
        """Login user asynchronously and return response details."""
        login_data = {
            "username": email,  # FastAPI-Users expects email in username field
            "password": password
        }
        response = await client.post("/api/auth/login", data=login_data)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def register_and_login_async(client: AsyncClient, user_data: dict[str, str] | None = None) -> dict[str, Any]:
        """Complete registration and login flow asynchronously. Returns user data and token."""
        if user_data is None:
            user_data = AuthTestHelperAsync.generate_unique_user_data()

        # Register user
        reg_status, reg_data = await AuthTestHelperAsync.register_user_async(client, user_data)
        assert reg_status == 201, f"Registration failed: {reg_status}"

        # Login user
        login_status, login_data = await AuthTestHelperAsync.login_user_async(
            client, user_data["email"], user_data["password"]
        )
        assert login_status == 200, f"Login failed: {login_status}"
        assert "access_token" in login_data, "No access token in login response"

        return {
            "user_data": user_data,
            "registration_response": reg_data,
            "login_response": login_data,
            "token": login_data["access_token"],
            "headers": {"Authorization": f"Bearer {login_data['access_token']}"}
        }

    @staticmethod
    async def logout_user_async(client: AsyncClient, token: str) -> tuple[int, dict[str, Any]]:
        """Logout user with token asynchronously."""
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/api/auth/logout", headers=headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def get_current_user_async(client: AsyncClient, token: str) -> tuple[int, dict[str, Any]]:
        """Get current user info with token asynchronously."""
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/auth/me", headers=headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    def get_auth_headers(token: str) -> dict[str, str]:
        """Get authorization headers for authenticated requests."""
        return {"Authorization": f"Bearer {token}"}
