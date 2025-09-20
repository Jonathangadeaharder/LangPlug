"""
Test /auth/logout with invalid token returns success=False.
"""
from __future__ import annotations

import pytest


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLogoutWithInvalidtoken_ThenFails(async_http_client):
    """Invalid input guard: logout with a bad token returns 401."""
    response = await async_http_client.post(
        "/api/auth/logout", headers={"Authorization": "Bearer BAD"}
    )

    assert response.status_code == 401

