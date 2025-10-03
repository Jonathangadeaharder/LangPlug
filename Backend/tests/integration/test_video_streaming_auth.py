"""
Integration test for video streaming authentication
Tests the get_user_from_query_token dependency
"""

import pytest
from httpx import AsyncClient

from core.auth import UserCreate


@pytest.mark.asyncio
class TestVideoStreamingAuthentication:
    """Test video streaming authentication via query token"""

    async def test_video_endpoint_with_query_token(self, async_client: AsyncClient):
        """Test that video endpoint accepts authentication via query parameter"""
        # Create a test user
        user_data = UserCreate(username="testvideouser", email="videotest@example.com", password="TestPass1234")

        # Register user
        response = await async_client.post(
            "/api/auth/register",
            json={"username": user_data.username, "email": user_data.email, "password": user_data.password},
        )
        assert response.status_code == 201

        # Login to get token
        response = await async_client.post(
            "/api/auth/login", data={"username": user_data.email, "password": user_data.password}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Test video endpoint with token as query parameter
        # Note: This will fail if video doesn't exist, but should NOT fail with 401
        response = await async_client.get(f"/api/videos/test_series/test_episode?token={token}")

        # Should NOT be 401 Unauthorized
        # Can be 404 (video not found), 200 (full video), or 206 (partial content/range request)
        assert response.status_code in [
            200,
            206,
            404,
        ], f"Expected 200/206/404, got {response.status_code}: {response.text}"

        # If we get here, authentication worked!
        if response.status_code == 404:
            # This is fine - video doesn't exist, but auth passed
            assert "not found" in response.json().get("detail", "").lower()
        elif response.status_code in [200, 206]:
            # Video streaming is working!
            pass

    async def test_video_endpoint_with_bearer_header(self, async_client: AsyncClient):
        """Test that video endpoint accepts Bearer token in Authorization header"""
        # Create a test user
        user_data = UserCreate(username="testvideouser2", email="videotest2@example.com", password="TestPass1234")

        # Register user
        response = await async_client.post(
            "/api/auth/register",
            json={"username": user_data.username, "email": user_data.email, "password": user_data.password},
        )
        assert response.status_code == 201

        # Login to get token
        response = await async_client.post(
            "/api/auth/login", data={"username": user_data.email, "password": user_data.password}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Test video endpoint with Bearer token in header
        response = await async_client.get(
            "/api/videos/test_series/test_episode", headers={"Authorization": f"Bearer {token}"}
        )

        # Should NOT be 401 Unauthorized
        # Can be 404 (video not found), 200 (full video), or 206 (partial content/range request)
        assert response.status_code in [
            200,
            206,
            404,
        ], f"Expected 200/206/404, got {response.status_code}: {response.text}"

    async def test_video_endpoint_without_token_fails(self, async_client: AsyncClient):
        """Test that video endpoint requires authentication"""
        response = await async_client.get("/api/videos/test_series/test_episode")

        # Should be 401 Unauthorized
        assert response.status_code == 401
        assert "authentication" in response.json().get("detail", "").lower()

    async def test_video_endpoint_with_invalid_token_fails(self, async_client: AsyncClient):
        """Test that video endpoint rejects invalid tokens"""
        response = await async_client.get("/api/videos/test_series/test_episode?token=invalid_token_here")

        # Should be 401 Unauthorized
        assert response.status_code == 401
