"""Targeted auth error cases following the protective testing guidelines."""

from __future__ import annotations

import pytest

from tests.assertion_helpers import assert_validation_error_response
from tests.helpers import AuthTestHelper


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLoginWithjson_payload_ThenRejects(async_http_client, url_builder):
    """Boundary: sending JSON instead of form data yields a 422 validation error."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)
    login_url = url_builder.url_for("auth:jwt.login")

    response = await async_http_client.post(
        login_url,
        json={"username": user_data["email"], "password": user_data["password"]},
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenloginWithoutpassword_ThenReturnsError(async_http_client, url_builder):
    """Invalid input: missing password triggers field-level validation failures."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_http_client, user_data)
    login_url = url_builder.url_for("auth:jwt.login")

    response = await async_http_client.post(
        login_url,
        data={"username": user_data["email"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert_validation_error_response(response, "password")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenloginWithoutusername_ThenReturnsError(async_http_client, url_builder):
    """Invalid input: missing username is rejected with validation detail."""
    login_url = url_builder.url_for("auth:jwt.login")

    response = await async_http_client.post(
        login_url,
        data={"password": "SecurePass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert_validation_error_response(response, "username")
