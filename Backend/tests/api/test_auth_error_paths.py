"""Focused auth error-path coverage respecting the CDD/TDD 80/20 rules."""

from __future__ import annotations

import pytest

from tests.assertion_helpers import assert_validation_error_response
from tests.auth_helpers import AuthResponseStructures, AuthTestHelper


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenRegisterMissingEmail_ThenReturnsvalidation_detail(async_http_client, url_builder):
    """Invalid input: missing email should return FastAPI validation errors."""
    payload = {
        "username": "missing_email",
        "password": "SecureTestPass123!",
    }
    register_url = url_builder.url_for("register:register")

    response = await async_http_client.post(register_url, json=payload)

    assert_validation_error_response(response, "email")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginbad_credentials_ThenReturnscontract_error(async_http_client, url_builder):
    """Invalid input: wrong password returns the documented bad credentials error."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)
    login_url = url_builder.url_for("auth:jwt.login")

    response = await async_http_client.post(
        login_url,
        data={"username": user_data["email"], "password": "WrongPass999!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == AuthResponseStructures.LOGIN_BAD_CREDENTIALS["status_code"]
    payload = response.json()
    # Handle both custom error format and FastAPI standard format
    if "error" in payload and "message" in payload["error"]:
        assert payload["error"]["message"] == "LOGIN_BAD_CREDENTIALS"
    elif "detail" in payload:
        assert payload["detail"] in {
            "LOGIN_BAD_CREDENTIALS",
            AuthResponseStructures.LOGIN_BAD_CREDENTIALS.get("detail"),
        }
    else:
        raise AssertionError(f"Unexpected error format: {payload}")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLogoutwithout_token_ThenReturnsunauthorized(async_http_client, url_builder):
    """Boundary: logout without Authorization header returns uniform 401 response."""
    logout_url = url_builder.url_for("auth:jwt.logout")
    response = await async_http_client.post(logout_url)

    assert response.status_code == AuthResponseStructures.UNAUTHORIZED["status_code"]
    www_authenticate = response.headers.get("www-authenticate")
    assert www_authenticate is None or "bearer" in www_authenticate.lower()
