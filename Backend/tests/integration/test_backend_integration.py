"""End-to-end happy-path flows using the in-process FastAPI app."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenuser_registration_login_and_meCalled_ThenSucceeds(async_http_client):
    """Happy path: user can register, login, and retrieve profile."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    status_code, profile = await AuthTestHelperAsync.get_current_user_async(
        async_http_client, flow["token"]
    )

    assert status_code == 200
    assert profile["username"] == flow["user_data"]["username"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlogout_invalidates_tokenCalled_ThenSucceeds(async_http_client):
    """Boundary: logout revokes access to authenticated endpoints."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)
    status_code, _ = await AuthTestHelperAsync.logout_user_async(async_http_client, flow["token"])
    assert status_code == 204

    profile_response = await async_http_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {flow['token']}"}
    )
    assert profile_response.status_code == 401
