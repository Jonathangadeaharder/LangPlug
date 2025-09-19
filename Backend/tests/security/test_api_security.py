"""Security posture tests that guard critical authentication and input handling paths."""
from __future__ import annotations

import os
import pytest

from tests.auth_helpers import AuthTestHelperAsync

# Skip this module in constrained environments where the async DB fixture hangs
pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy security tests in constrained sandbox",
)


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_Whenvocabulary_statsWithoutauthentication_ThenReturnsError(async_client) -> None:
    """Unauthenticated users should receive a 401 when accessing protected resources."""
    response = await async_client.get("/api/vocabulary/library/stats")

    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_invalid_BearerToken_is_rejected(async_client) -> None:
    """A malformed bearer token must not grant access."""
    response = await async_client.get(
        "/api/vocabulary/library/stats",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_Whensql_injection_payloadCalled_ThenReturnssafe_response(async_client) -> None:
    """Representative SQL injection payloads should not surface in responses or crash the API."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    payload = "'; DROP TABLE vocabulary; --"

    response = await async_client.get(
        "/api/vocabulary/search",
        params={"q": payload},
        headers=flow["headers"],
    )

    assert response.status_code in {200, 400, 404}
    assert payload.lower() not in response.text.lower()


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_Whenxss_payload_is_escapedCalled_ThenSucceeds(async_client) -> None:
    """Potential XSS payloads must be escaped in responses."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    payload = "<script>alert('oops')</script>"

    response = await async_client.get(
        "/api/vocabulary/search",
        params={"q": payload},
        headers=flow["headers"],
    )

    assert response.status_code in {200, 400, 404}
    assert payload not in response.text


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_WhenLogoutCalled_ThenRevokesaccess(async_client) -> None:
    """After logout the token should no longer authorize requests."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    logout = await async_client.post("/api/auth/logout", headers=flow["headers"])
    assert logout.status_code in {200, 204}

    me_response = await async_client.get("/api/auth/me", headers=flow["headers"])
    assert me_response.status_code == 401
