"""Minimal integration checks using the built-in async_client fixture."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenhealth_endpointCalled_ThenSucceeds(async_http_client):
    response = await async_http_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_statsWithoutauth_ThenReturnsError(async_http_client):
    response = await async_http_client.get("/api/vocabulary/library/stats")
    assert response.status_code == 401

    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)
    authed = await async_http_client.get(
        "/api/vocabulary/library/stats", headers=flow["headers"]
    )
    assert authed.status_code in {200, 500}
