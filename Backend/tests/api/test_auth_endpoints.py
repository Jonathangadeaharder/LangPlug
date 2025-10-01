"""Behavioral auth endpoint tests following the CDD/TDD policy.

Covers the 80/20 protective scenarios for the auth contract:
- Happy path registration + login
- Invalid input rejection
- Boundary protection for duplicate identities and malformed form data
"""

from __future__ import annotations

import pytest

from tests.assertion_helpers import assert_validation_error_response
from tests.auth_helpers import AuthTestHelper


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenRegisterCalled_ThenCreatesActiveUser(async_http_client):
    """Happy path: registration returns a contract-compliant user payload."""
    user_data = AuthTestHelper.generate_unique_user_data()

    status_code, payload = await AuthTestHelper.register_user_async(async_http_client, user_data)

    assert status_code == 201
    assert payload["username"] == user_data["username"]
    assert payload["email"] == user_data["email"]
    assert isinstance(payload["id"], int)
    assert payload["is_active"] is True
    assert payload["is_superuser"] is False


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenRegisterWithMissingEmail_ThenRejects(async_http_client):
    """Invalid input: missing email triggers FastAPI validation 422 response."""
    user_data = AuthTestHelper.generate_unique_user_data()
    payload = {"username": user_data["username"], "password": user_data["password"]}

    response = await async_http_client.post("/api/auth/register", json=payload)

    assert_validation_error_response(response, "email")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenRegisterWithDuplicateUsername_ThenPrevents(async_http_client):
    """Boundary: duplicate username surfaces a 400 contract error."""
    user_data = AuthTestHelper.generate_unique_user_data()

    first_status, _ = await AuthTestHelper.register_user_async(async_http_client, user_data)
    assert first_status == 201

    second_response = await async_http_client.post("/api/auth/register", json=user_data)
    assert second_response.status_code == 400


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginCalled_ThenReturnsBearerToken(async_http_client):
    """Happy path login returns bearer token per contract."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)

    status_code, payload = await AuthTestHelper.login_user_async(
        async_http_client, user_data["email"], user_data["password"]
    )

    assert status_code == 200
    assert payload["token_type"].lower() == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["access_token"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginWithWrongPassword_ThenRejects(async_http_client):
    """Invalid input: wrong password returns the standard 400 failure."""
    user_data = AuthTestHelper.generate_unique_user_data()

    await AuthTestHelper.register_user_async(async_http_client, user_data)

    status_code, _ = await AuthTestHelper.login_user_async(async_http_client, user_data["email"], "TotallyWrong123!")

    assert status_code == 400


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenloginWithoutform_encoded_payload_ThenReturnsError(async_http_client):
    """Boundary: JSON payload is rejected to guard contract expectations."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)

    response = await async_http_client.post(
        "/api/auth/login",
        json={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )

    # FastAPI-Users expects form-encoded data, so JSON should return 422 validation error
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for wrong content type), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLogoutCalled_ThenRevokestoken(async_http_client):
    """Happy path logout removes bearer token access."""
    flow = await AuthTestHelper.register_and_login_async(async_http_client)

    status_code, _ = await AuthTestHelper.logout_user_async(async_http_client, flow["token"])

    assert status_code == 204


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenlogoutWithoutvalid_token_ThenReturnsError(async_http_client):
    """Invalid input: logout without a real token yields 401 unauthorized."""
    response = await async_http_client.post("/api/auth/logout", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenmeCalled_ThenReturnscurrent_user_profile(async_http_client):
    """Happy path query of /me returns the authenticated user contract payload."""
    flow = await AuthTestHelper.register_and_login_async(async_http_client)

    status_code, payload = await AuthTestHelper.get_current_user_async(async_http_client, flow["token"])

    assert status_code == 200
    assert payload["username"] == flow["user_data"]["username"]
    assert payload["is_active"] is True
    assert payload["is_superuser"] is False


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenmeWithoutauthentication_ThenReturnsError(async_http_client):
    """Invalid input: /me without credentials returns contract 401."""
    response = await async_http_client.get("/api/auth/me")

    assert response.status_code == 401
