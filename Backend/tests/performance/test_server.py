"""Server smoke tests that validate critical endpoints respond as expected."""
from __future__ import annotations

import os
import pytest

from core.app import create_app
from httpx import ASGITransport, AsyncClient
from tests.auth_helpers import AuthTestHelper


@pytest.fixture
async def async_client_no_db():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_Whenhealth_includes_versionCalled_ThenSucceeds(async_client_no_db) -> None:
    """Health endpoint should advertise the service version."""
    response = await async_client_no_db.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "version" in payload


@pytest.mark.timeout(30)
@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping auth endpoint check in constrained sandbox (requires DB)",
)
async def test_WhenloginWithoutform_encoding_ThenReturnsError(async_client_no_db) -> None:
    """Submitting JSON to the login endpoint should trigger validation failure."""
    response = await async_client_no_db.post(
        "/api/auth/login",
        json={"username": "user@example.com", "password": "Password123!"},
    )

    assert response.status_code in {400, 422}


@pytest.mark.timeout(30)
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy performance test in constrained sandbox",
)
def test_Whenregister_and_login_via_sync_clientCalled_ThenSucceeds(client) -> None:
    """The synchronous test client should handle an end-to-end auth flow."""
    user_data = AuthTestHelper.generate_unique_user_data()

    reg_status, _ = AuthTestHelper.register_user(client, user_data)
    login_status, login_payload = AuthTestHelper.login_user(
        client,
        email=user_data["email"],
        password=user_data["password"],
    )

    assert reg_status == 201
    assert login_status == 200
    assert login_payload["token_type"].lower() == "bearer"
