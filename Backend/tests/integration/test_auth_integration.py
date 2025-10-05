"""
Integration tests for authentication flow
"""

import pytest
from httpx import AsyncClient

from tests.auth_helpers import AuthTestHelperAsync


class TestAuthenticationIntegration:
    """Integration tests for authentication functionality"""

    @pytest.mark.asyncio
    async def test_health_endpoint_reports_healthy(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_register_and_login_returns_bearer_token(self, async_client: AsyncClient) -> None:
        auth_flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        login_response = auth_flow["login_response"]
        assert login_response["token_type"] == "bearer"
        assert "access_token" in login_response

    @pytest.mark.asyncio
    async def test_authenticated_user_profile_matches_registration(self, async_client: AsyncClient) -> None:
        auth_flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        response = await async_client.get("/api/auth/me", headers=auth_flow["headers"])
        assert response.status_code == 200, f"Token validation failed: {response.text}"

        me_data = response.json()
        assert me_data["email"] == auth_flow["user_data"]["email"]
        assert me_data["is_active"] is True

    @pytest.mark.asyncio
    async def test_login_rejects_username_credentials(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 400, f"Expected 400 for invalid credentials, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_login_rejects_invalid_password(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/api/auth/login",
            data={"username": "admin@langplug.com", "password": "wrong_password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 400, f"Expected 400 for bad credentials, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_auth_me_requires_valid_token(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/auth/me")
        assert response.status_code == 401

        response = await async_client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
