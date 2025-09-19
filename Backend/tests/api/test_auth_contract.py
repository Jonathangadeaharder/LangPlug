"""Auth contract verification aligned with the CDD/TDD policies.

Each test focuses on the observable contract:
1. Happy path ensures the documented response schema is honoured.
2. Invalid input returns the documented validation/errors.
3. Boundary protection prevents subtle regressions (duplicates, wrong formats).
"""
from __future__ import annotations

import uuid

import pytest

from tests.auth_helpers import AuthResponseStructures, AuthTestHelper, validate_auth_response


def _assert_user_payload(payload: dict[str, str], expected_username: str, expected_email: str) -> None:
    """Validate common user response contract requirements."""
    validate_auth_response(payload, AuthResponseStructures.REGISTRATION_SUCCESS)
    assert payload["username"] == expected_username
    assert payload["email"] == expected_email
    uuid.UUID(payload["id"])  # raises if not UUID formatted


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenRegisterCalledWithValidData_ThenReturnsUserResponse(async_client):
    user_data = AuthTestHelper.generate_unique_user_data()

    status_code, payload = await AuthTestHelper.register_user_async(async_client, user_data)

    assert status_code == 201
    _assert_user_payload(payload, user_data["username"], user_data["email"])


@pytest.mark.anyio
@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "payload, expected_missing_field",
    [
        ({"email": "test@example.com", "password": "SecurePass123!"}, "username"),
        ({"username": "missing_email", "password": "SecurePass123!"}, "email"),
        ({"username": "", "email": "bad@example.com", "password": "SecurePass123!"}, "username"),
    ],
)
async def test_WhenRegisterCalledWithInvalidPayload_ThenReturnsValidationError(async_client, payload, expected_missing_field):
    response = await async_client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    response_data = response.json()
    # Handle both FastAPI standard and custom error formats
    if "detail" in response_data:
        errors = response_data["detail"]
        assert any(expected_missing_field in ":".join(map(str, err["loc"])) for err in errors)
    else:
        # Custom error format
        assert "error" in response_data


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenRegisterCalledWithDuplicateUser_ThenRejectsDuplication(async_client):
    user_data = AuthTestHelper.generate_unique_user_data()
    status_code, _ = await AuthTestHelper.register_user_async(async_client, user_data)
    assert status_code == 201

    duplicate_response = await async_client.post("/api/auth/register", json=user_data)
    assert duplicate_response.status_code == 400


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginCalledWithValidCredentials_ThenReturnsBearerToken(async_client):
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_client, user_data)

    status_code, payload = await AuthTestHelper.login_user_async(
        async_client, user_data["email"], user_data["password"]
    )

    assert status_code == 200
    validate_auth_response(payload, AuthResponseStructures.LOGIN_SUCCESS)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginCalledWithBadCredentials_ThenRejectsWithError(async_client):
    status_code, payload = await AuthTestHelper.login_user_async(
        async_client, "no_user@example.com", "SuperSecret123!"
    )

    assert status_code == 400
    assert "detail" in payload  # FastAPI-Users returns 'detail' instead of 'error'


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLogoutCalledWithValidToken_ThenReturnsNoContent(async_client):
    flow = await AuthTestHelper.register_and_login_async(async_client)

    status_code, body = await AuthTestHelper.logout_user_async(async_client, flow["token"])

    assert status_code == 204
    assert body == {}


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenMeCalledWithoutAuth_ThenReturnsUnauthorized(async_client):
    response = await async_client.get("/api/auth/me")

    assert response.status_code == AuthResponseStructures.UNAUTHORIZED["status_code"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenMeCalledWithValidToken_ThenReturnsUserProfile(async_client):
    flow = await AuthTestHelper.register_and_login_async(async_client)

    status_code, payload = await AuthTestHelper.get_current_user_async(async_client, flow["token"])

    assert status_code == AuthResponseStructures.USER_INFO_SUCCESS["status_code"]
    validate_auth_response(payload, AuthResponseStructures.USER_INFO_SUCCESS)
    assert payload["username"] == flow["user_data"]["username"]