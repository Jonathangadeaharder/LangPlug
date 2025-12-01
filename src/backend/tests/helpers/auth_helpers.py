"""Clean, modern authentication helpers following test standards."""

from __future__ import annotations

from typing import Any

import httpx

from .assertions import assert_auth_response_structure, assert_json_response
from .data_builders import TestUser, UserBuilder


class AuthHelper:
    """Synchronous authentication helper for test clients."""

    def __init__(self, client: httpx.Client):
        self.client = client

    def create_test_user(self, **overrides) -> TestUser:
        """Create a test user with optional field overrides."""
        user = UserBuilder().build()
        for key, value in overrides.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return user

    def register_user(self, user: TestUser = None) -> tuple[TestUser, dict[str, Any]]:
        """Register a user and return user data and response."""
        if user is None:
            user = self.create_test_user()

        response = self.client.post("/api/auth/register", json=user.to_dict())
        data = assert_json_response(response, 201)

        return user, data

    def login_user(self, user: TestUser) -> tuple[str, dict[str, Any]]:
        """Login a user and return access token and response data."""
        login_data = {
            "username": user.email,  # FastAPI-Users expects email in username field
            "password": user.password,
        }

        # Use the token endpoint for bearer auth
        response = self.client.post("/api/auth/token/login", data=login_data)
        data = assert_json_response(response, 200)
        assert_auth_response_structure(data)

        return data["access_token"], data

    def create_authenticated_user(self, user: TestUser = None) -> tuple[TestUser, str, dict[str, str]]:
        """Complete flow: create user, register, login, return user, token, and headers."""
        if user is None:
            user = self.create_test_user()

        # Register user
        _, _reg_data = self.register_user(user)

        # Login user
        token, _login_data = self.login_user(user)

        # Create auth headers
        headers = {"Authorization": f"Bearer {token}"}

        return user, token, headers

    def get_auth_headers(self, user: TestUser = None) -> dict[str, str]:
        """Quick helper to get auth headers for a user."""
        _, _, headers = self.create_authenticated_user(user)
        return headers

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify token by calling /me endpoint."""
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/auth/me", headers=headers)
        return assert_json_response(response, 200)

    def logout_user(self, token: str) -> dict[str, Any]:
        """
        Logout user with token.

        Note: FastAPI-Users logout returns 204 No Content.
        JWT tokens are stateless and cannot be invalidated without a blacklist.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post("/api/auth/token/logout", headers=headers)
        # Logout returns 204 No Content (no body)
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
        return {"success": True, "message": "Logged out"}


class AsyncAuthHelper:
    """Asynchronous authentication helper for async test clients."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def create_test_user(self, **overrides) -> TestUser:
        """Create a test user with optional field overrides."""
        user = UserBuilder().build()
        for key, value in overrides.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return user

    async def register_user(self, user: TestUser = None) -> tuple[TestUser, dict[str, Any]]:
        """Register a user and return user data and response."""
        if user is None:
            user = self.create_test_user()

        response = await self.client.post("/api/auth/register", json=user.to_dict())
        data = assert_json_response(response, 201)

        return user, data

    async def login_user(self, user: TestUser) -> tuple[str, dict[str, Any]]:
        """Login a user and return access token and response data."""
        login_data = {
            "username": user.email,  # FastAPI-Users expects email in username field
            "password": user.password,
        }

        # Use the token endpoint for bearer auth
        response = await self.client.post("/api/auth/token/login", data=login_data)
        data = assert_json_response(response, 200)
        assert_auth_response_structure(data)

        return data["access_token"], data

    async def create_authenticated_user(self, user: TestUser = None) -> tuple[TestUser, str, dict[str, str]]:
        """Complete flow: create user, register, login, return user, token, and headers."""
        if user is None:
            user = self.create_test_user()

        # Register user
        _, _reg_data = await self.register_user(user)

        # Login user
        token, _login_data = await self.login_user(user)

        # Create auth headers
        headers = {"Authorization": f"Bearer {token}"}

        return user, token, headers

    async def get_auth_headers(self, user: TestUser = None) -> dict[str, str]:
        """Quick helper to get auth headers for a user."""
        _, _, headers = await self.create_authenticated_user(user)
        return headers

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Verify token by calling /me endpoint."""
        headers = {"Authorization": f"Bearer {token}"}
        response = await self.client.get("/api/auth/me", headers=headers)
        return assert_json_response(response, 200)

    async def logout_user(self, token: str) -> dict[str, Any]:
        """
        Logout user with token.

        Note: FastAPI-Users logout returns 204 No Content.
        JWT tokens are stateless and cannot be invalidated without a blacklist.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = await self.client.post("/api/auth/token/logout", headers=headers)
        # Logout returns 204 No Content (no body)
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
        return {"success": True, "message": "Logged out"}


# Test scenarios for authentication testing
class AuthTestScenarios:
    """Predefined test scenarios for authentication testing."""

    @staticmethod
    def invalid_registration_data() -> list[tuple[dict[str, Any], str]]:
        """Return list of invalid registration data and expected error descriptions."""
        return [
            ({"username": "", "password": "ValidPass123!"}, "empty username"),
            ({"username": "valid", "password": ""}, "empty password"),
            ({"username": "valid", "password": "weak"}, "weak password"),
            ({"username": "ab", "password": "ValidPass123!"}, "username too short"),
            ({}, "missing required fields"),
        ]

    @staticmethod
    def invalid_login_data() -> list[tuple[dict[str, Any], str]]:
        """Return list of invalid login data and expected error descriptions."""
        return [
            ({"username": "", "password": "anything"}, "empty username"),
            ({"username": "valid@example.com", "password": ""}, "empty password"),
            ({"username": "nonexistent@example.com", "password": "ValidPass123!"}, "user not found"),
            ({"username": "valid@example.com", "password": "wrongpassword"}, "invalid password"),
        ]

    @staticmethod
    def create_admin_user() -> TestUser:
        """Create an admin user for testing admin endpoints."""
        return UserBuilder().as_admin().with_username("testadmin").with_email("admin@example.com").build()

    @staticmethod
    def create_inactive_user() -> TestUser:
        """Create an inactive user for testing access restrictions."""
        return UserBuilder().as_inactive().with_username("inactive").with_email("inactive@example.com").build()


# Fixtures for common authentication setups
def create_auth_fixtures():
    """Helper to create common authentication fixtures for tests."""
    return {
        "basic_user": AuthTestScenarios.create_admin_user,
        "admin_user": AuthTestScenarios.create_admin_user,
        "inactive_user": AuthTestScenarios.create_inactive_user,
        "invalid_registration_data": AuthTestScenarios.invalid_registration_data,
        "invalid_login_data": AuthTestScenarios.invalid_login_data,
    }
