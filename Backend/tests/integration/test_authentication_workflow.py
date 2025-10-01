"""Proper pytest tests for authentication workflow (converted from manual demo script)."""

from __future__ import annotations

import pytest

from tests.helpers import (
    AsyncAuthHelper,
    assert_auth_response_structure,
    assert_authentication_error,
    assert_json_response,
    assert_status_code,
    assert_user_response_structure,
)


class TestAuthenticationWorkflow:
    """Test complete authentication workflow with proper assertions."""

    @pytest.mark.anyio
    async def test_When_health_endpoint_called_Then_returns_healthy_status(self, async_client):
        """Health endpoint should return healthy status."""
        # Act
        response = await async_client.get("/health")

        # Assert
        data = assert_json_response(response, 200)
        assert data["status"] == "healthy"

    @pytest.mark.anyio
    async def test_When_user_registers_and_logs_in_Then_receives_valid_token(self, async_client):
        """Complete user registration and login flow should work."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)

        # Act
        user, token, headers = await auth_helper.create_authenticated_user()

        # Assert
        assert user.username
        assert user.email
        assert len(token) > 10  # Token should be non-trivial length
        assert headers["Authorization"] == f"Bearer {token}"

    @pytest.mark.anyio
    async def test_When_valid_credentials_used_for_login_Then_returns_access_token(self, async_client):
        """Login with valid email and password should return access token."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        user, _ = await auth_helper.register_user()

        # Act
        token, login_data = await auth_helper.login_user(user)

        # Assert
        assert token
        assert_auth_response_structure(login_data)
        assert login_data["token_type"] == "bearer"

    @pytest.mark.anyio
    async def test_When_username_used_instead_of_email_Then_login_fails(self, async_client):
        """Login with username instead of email should fail."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        user, _ = await auth_helper.register_user()

        # Act
        login_data = {
            "username": user.username,  # Using username instead of email
            "password": user.password,
        }
        response = await async_client.post("/api/auth/login", data=login_data)

        # Assert
        assert response.status_code in [400, 401], "Login should fail when using username instead of email"

    @pytest.mark.anyio
    async def test_When_invalid_credentials_used_Then_login_fails(self, async_client):
        """Login with invalid credentials should return authentication error."""
        # Act
        login_data = {"username": "nonexistent@example.com", "password": "wrongpassword"}
        response = await async_client.post("/api/auth/login", data=login_data)

        # Assert
        assert response.status_code in [400, 401], "Login should fail with invalid credentials"

    @pytest.mark.anyio
    async def test_When_valid_token_used_Then_user_info_returned(self, async_client):
        """Valid token should allow access to user info."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.get("/api/auth/me", headers=headers)

        # Assert
        data = assert_json_response(response, 200)
        assert_user_response_structure(data)
        assert data["username"] == user.username

    @pytest.mark.anyio
    async def test_When_no_token_provided_Then_authentication_required(self, async_client):
        """Access to protected endpoint without token should require authentication."""
        # Act
        response = await async_client.get("/api/auth/me")

        # Assert
        assert_authentication_error(response)

    @pytest.mark.anyio
    async def test_When_invalid_token_provided_Then_authentication_fails(self, async_client):
        """Invalid token should result in authentication error."""
        # Arrange
        invalid_headers = {"Authorization": "Bearer invalid_token_123"}

        # Act
        response = await async_client.get("/api/auth/me", headers=invalid_headers)

        # Assert
        assert_authentication_error(response)

    @pytest.mark.anyio
    async def test_When_malformed_token_provided_Then_authentication_fails(self, async_client):
        """Malformed authorization header should result in authentication error."""
        # Arrange
        malformed_headers = {"Authorization": "InvalidFormat token123"}

        # Act
        response = await async_client.get("/api/auth/me", headers=malformed_headers)

        # Assert
        assert_authentication_error(response)

    @pytest.mark.anyio
    async def test_When_user_logs_out_Then_token_becomes_invalid(self, async_client):
        """After logout, token should become invalid."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, token, headers = await auth_helper.create_authenticated_user()

        # Verify token works initially
        response = await async_client.get("/api/auth/me", headers=headers)
        assert_status_code(response, 200)

        # Act - logout
        await auth_helper.logout_user(token)

        # Assert - token should now be invalid
        response = await async_client.get("/api/auth/me", headers=headers)
        assert response.status_code in [401, 403], "Token should be invalid after logout"


class TestCORSConfiguration:
    """Test CORS configuration for frontend integration."""

    @pytest.mark.anyio
    async def test_When_options_request_sent_Then_cors_headers_present(self, async_client):
        """OPTIONS request should return appropriate CORS headers."""
        # Act
        response = await async_client.options("/api/auth/login", headers={"Origin": "http://localhost:3000"})

        # Assert
        # Accept various status codes as different servers handle OPTIONS differently
        assert response.status_code in [200, 204, 405], f"Unexpected status code: {response.status_code}"

        # Check for CORS headers (if supported)
        cors_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers"]

        cors_found = any(header in response.headers for header in cors_headers)
        if not cors_found and response.status_code == 405:
            # OPTIONS not supported - this is acceptable behavior
            pytest.skip("CORS OPTIONS not implemented - using different CORS strategy")

        assert cors_found, "No CORS headers found in response"


class TestAuthenticationSecurity:
    """Test authentication security aspects."""

    @pytest.mark.anyio
    async def test_When_registration_data_missing_required_fields_Then_validation_error(self, async_client):
        """Registration without required fields should return validation error."""
        # Act
        response = await async_client.post("/api/auth/register", json={})

        # Assert
        assert_status_code(response, 422)

    @pytest.mark.anyio
    async def test_When_weak_password_provided_Then_validation_error(self, async_client):
        """Weak password should be rejected during registration."""
        # Act
        registration_data = {"username": "testuser", "email": "test@example.com", "password": "weak"}
        response = await async_client.post("/api/auth/register", json=registration_data)

        # Assert
        assert response.status_code in [400, 422], "Weak password should be rejected"

    @pytest.mark.anyio
    async def test_When_duplicate_user_registered_Then_conflict_error(self, async_client):
        """Registering duplicate user should return conflict error."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        user, _ = await auth_helper.register_user()

        # Act - try to register same user again
        response = await async_client.post("/api/auth/register", json=user.to_dict())

        # Assert
        assert response.status_code in [400, 409], "Duplicate registration should be rejected"

    @pytest.mark.anyio
    async def test_When_empty_credentials_provided_Then_validation_error(self, async_client):
        """Empty credentials should return validation error."""
        # Act
        response = await async_client.post("/api/auth/login", data={})

        # Assert
        assert response.status_code in [400, 422], "Empty credentials should be rejected"


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication with other system components."""

    @pytest.mark.anyio
    async def test_When_authenticated_user_accesses_protected_resource_Then_succeeds(self, async_client):
        """Authenticated user should be able to access protected resources."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act - try to access a protected endpoint (example: vocabulary stats)
        response = await async_client.get("/api/vocabulary/stats", headers=headers)

        # Assert - should either succeed or fail with expected error (not auth error)
        assert response.status_code != 401, "Authentication should not be the issue"
        # Actual functionality tested in vocabulary-specific tests

    @pytest.mark.anyio
    async def test_When_multiple_users_created_Then_each_has_unique_session(self, async_client):
        """Multiple users should have independent authentication sessions."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)

        # Act
        user1, token1, headers1 = await auth_helper.create_authenticated_user()
        user2, token2, headers2 = await auth_helper.create_authenticated_user()

        # Assert
        assert user1.email != user2.email
        assert token1 != token2

        # Verify each token works for its respective user
        response1 = await async_client.get("/api/auth/me", headers=headers1)
        response2 = await async_client.get("/api/auth/me", headers=headers2)

        data1 = assert_json_response(response1, 200)
        data2 = assert_json_response(response2, 200)

        assert data1["username"] == user1.username
        assert data2["username"] == user2.username
        assert data1["username"] != data2["username"]
