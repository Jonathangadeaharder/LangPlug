"""
Test /auth/logout with invalid token returns success=False.
"""
from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_logout_invalid_token(async_client):
    r = await async_client.post("/api/auth/logout", headers={"Authorization": "Bearer BAD"})
    assert r.status_code == 200
    assert r.json().get("success") is False

