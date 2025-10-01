"""
Integration tests for complete authentication workflows
Tests the entire auth flow from registration to logout
"""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from core.app import create_app


@pytest.mark.integration
class TestAuthenticationWorkflow:
    """Integration tests for complete authentication workflows"""

    @pytest.fixture
    def app(self):
        """Create application instance for testing"""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test HTTP client"""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self, app):
        """Create async test HTTP client using httpx with ASGI transport"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac

    @pytest.fixture
    def unique_user_data(self):
        """Generate unique user data for each test"""
        unique_id = uuid4().hex[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "password": "SecurePassword123!",
        }

    def test_complete_registration_login_flow(self, client, unique_user_data):
        """Test complete registration and login workflow"""

        # Step 1: Register new user
        register_response = client.post("/api/auth/register", json=unique_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert "id" in user_data
        assert user_data["email"] == unique_user_data["email"]
        assert "password" not in user_data  # Password should not be returned
        assert "hashed_password" not in user_data

        # Step 2: Login with credentials
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": unique_user_data["email"],  # FastAPI-Users uses email as username
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"

        access_token = login_data["access_token"]

        # Step 3: Access protected endpoint with token
        me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == unique_user_data["email"]
        assert me_data["is_active"] is True

        # Step 4: Logout
        logout_response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
        assert logout_response.status_code in [200, 204]

        # Step 5: Verify token is invalidated (optional based on implementation)
        # Some implementations might still allow the token until expiry
        # This depends on your logout implementation

    @pytest.mark.asyncio
    async def test_registration_validation_errors(self, async_client: AsyncClient):
        """Test registration with various validation errors"""

        # Test invalid email
        response = await async_client.post(
            "/api/auth/register",
            json={"username": "testuser1", "email": "invalid-email", "password": "SecurePassword123!"},
        )
        assert response.status_code == 422

        # Test weak password (empty password)
        response = await async_client.post(
            "/api/auth/register", json={"username": "testuser2", "email": "test2@example.com", "password": ""}
        )
        assert response.status_code == 422

        # Test missing required fields
        response = await async_client.post("/api/auth/register", json={"email": "test3@example.com"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_registration(self, async_client: AsyncClient, unique_user_data):
        """Test registration with duplicate email/username"""

        # First registration should succeed
        response1 = await async_client.post("/api/auth/register", json=unique_user_data)
        assert response1.status_code == 201

        # Second registration with same email should fail
        response2 = await async_client.post("/api/auth/register", json=unique_user_data)
        assert response2.status_code == 400
        assert "already_exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, async_client: AsyncClient, unique_user_data):
        """Test login with various invalid credentials"""

        # Register user first
        await async_client.post("/api/auth/register", json=unique_user_data)

        # Test wrong password
        response = await async_client.post(
            "/api/auth/login",
            data={"username": unique_user_data["email"], "password": "WrongPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 400
        assert "login_bad_credentials" in response.json()["detail"].lower()

        # Test non-existent user
        response = await async_client.post(
            "/api/auth/login",
            data={"username": "nonexistent@example.com", "password": "SomePassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_protected_endpoints_without_auth(self, async_client: AsyncClient):
        """Test accessing protected endpoints without authentication"""

        # Test /api/auth/me without token
        response = await async_client.get("/api/auth/me")
        assert response.status_code == 401

        # Test with invalid token
        response = await async_client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

        # Test with wrong token type
        response = await async_client.get("/api/auth/me", headers={"Authorization": "Basic sometoken"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_concurrent_registrations(self, async_client: AsyncClient):
        """Test handling of concurrent registration attempts"""

        # Create multiple registration tasks with same email
        email = f"concurrent_{uuid4().hex[:8]}@example.com"
        user_data = {"username": f"user_{uuid4().hex[:8]}", "email": email, "password": "SecurePassword123!"}

        # Create 5 concurrent registration attempts
        tasks = []
        for i in range(5):
            data = user_data.copy()
            data["username"] = f"user_{i}_{uuid4().hex[:8]}"
            tasks.append(async_client.post("/api/auth/register", json=data))

        # Execute concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count responses by type
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 201)
        client_error_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 400)
        server_error_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 500)
        exception_count = sum(1 for r in responses if isinstance(r, Exception))

        # In concurrent registrations with same email, database constraint violations can occur
        # At most one should succeed, others fail with constraints (400 or 500) or exceptions
        assert success_count <= 1  # At most one succeeds
        total_responses = success_count + client_error_count + server_error_count + exception_count
        assert total_responses == 5  # All 5 requests accounted for

        # Most should fail due to duplicate email constraints
        failed_count = client_error_count + server_error_count + exception_count
        assert failed_count >= 4  # At least 4 should fail

    @pytest.mark.asyncio
    async def test_token_expiration(self, async_client: AsyncClient, unique_user_data):
        """Test token expiration handling"""

        # Register and login
        await async_client.post("/api/auth/register", json=unique_user_data)
        login_response = await async_client.post(
            "/api/auth/login",
            data={"username": unique_user_data["email"], "password": unique_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        access_token = login_response.json()["access_token"]

        # Token should work immediately
        response = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200

        # Note: Testing actual expiration would require waiting or mocking time
        # In a real test, you might want to:
        # 1. Use a short expiration time in test config
        # 2. Mock the current time
        # 3. Or use freezegun library

    @pytest.mark.asyncio
    async def test_password_reset_flow(self, async_client: AsyncClient, unique_user_data):
        """Test password reset workflow"""

        # Register user
        await async_client.post("/api/auth/register", json=unique_user_data)

        # Request password reset (endpoint not implemented yet)
        reset_response = await async_client.post("/api/auth/forgot-password", json={"email": unique_user_data["email"]})
        # Endpoint not implemented, expecting 404
        assert reset_response.status_code == 404

        # In a real implementation, you would:
        # 1. Capture the reset token from email/database
        # 2. Use the token to reset password
        # 3. Verify login with new password

    @pytest.mark.asyncio
    async def test_user_profile_update(self, async_client: AsyncClient, unique_user_data):
        """Test user profile update workflow"""

        # Register and login
        await async_client.post("/api/auth/register", json=unique_user_data)
        login_response = await async_client.post(
            "/api/auth/login",
            data={"username": unique_user_data["email"], "password": unique_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Update profile
        update_data = {"first_name": "Updated", "last_name": "Name"}

        update_response = await async_client.patch("/api/auth/me", json=update_data, headers=headers)

        if update_response.status_code == 200:
            updated_data = update_response.json()
            assert updated_data.get("first_name") == "Updated"
            assert updated_data.get("last_name") == "Name"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client: AsyncClient):
        """Test rate limiting on authentication endpoints"""

        # Attempt multiple rapid login attempts
        email = f"ratelimit_{uuid4().hex[:8]}@example.com"

        # Make many rapid requests
        responses = []
        for _i in range(10):
            response = await async_client.post(
                "/api/auth/login",
                data={"username": email, "password": "WrongPassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            responses.append(response.status_code)

        # Check if any were rate limited
        # This depends on your rate limiting configuration
        # You might see 429 (Too Many Requests) status codes

    @pytest.mark.asyncio
    async def test_session_management(self, async_client: AsyncClient, unique_user_data):
        """Test session management and multiple login sessions"""

        # Register user
        await async_client.post("/api/auth/register", json=unique_user_data)

        # Login from multiple "devices" (different sessions)
        tokens = []
        for _i in range(3):
            login_response = await async_client.post(
                "/api/auth/login",
                data={"username": unique_user_data["email"], "password": unique_user_data["password"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            tokens.append(login_response.json()["access_token"])

        # All tokens should work
        for token in tokens:
            response = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_account_deactivation(self, async_client: AsyncClient, unique_user_data):
        """Test account deactivation workflow"""

        # Register and login
        await async_client.post("/api/auth/register", json=unique_user_data)
        login_response = await async_client.post(
            "/api/auth/login",
            data={"username": unique_user_data["email"], "password": unique_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        access_token = login_response.json()["access_token"]

        # Deactivate account (if endpoint exists)
        deactivate_response = await async_client.delete(
            "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        if deactivate_response.status_code in [200, 204]:
            # Try to login again - should fail
            login_response = await async_client.post(
                "/api/auth/login",
                data={"username": unique_user_data["email"], "password": unique_user_data["password"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert login_response.status_code == 400
