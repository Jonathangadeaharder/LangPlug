"""Targeted auth error cases following the protective testing guidelines."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelper
from tests.assertion_helpers import assert_validation_error_response


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginWithjson_payload_ThenRejects(async_http_client):
    """Boundary: sending JSON instead of form data yields a 422 validation error."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)

    response = await async_http_client.post(
        "/api/auth/login",
        json={"username": user_data["email"], "password": user_data["password"]},
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenloginWithoutpassword_ThenReturnsError(async_http_client):
    """Invalid input: missing password triggers field-level validation failures."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)

    response = await async_http_client.post(
        "/api/auth/login",
        data={"username": user_data["email"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert_validation_error_response(response, "password")
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenloginWithoutusername_ThenReturnsError(async_http_client):
    """Invalid input: missing username is rejected with validation detail."""
    response = await async_http_client.post(
        "/api/auth/login",
        data={"password": "SecurePass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert_validation_error_response(response, "username")


