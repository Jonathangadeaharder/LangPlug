"""Validation error contract tests following the 80/20 guideline."""

from __future__ import annotations

import pytest

from tests.helpers import AsyncAuthHelper


def _extract_validation_errors(data: dict) -> list:
    """Extract validation errors from either standard FastAPI or custom error format."""
    # Standard FastAPI format: {"detail": [...]}
    if "detail" in data:
        return data["detail"]
    # Custom error format: {"error": {"details": [...]}}
    if "error" in data and "details" in data["error"]:
        return data["error"]["details"]
    return []


@pytest.mark.asyncio
@pytest.mark.timeout(30)
class TestPasswordValidationErrorMessages:
    """Verify password validation returns user-friendly error messages, not just 'Value error'."""

    async def test_short_password_returns_helpful_message(self, async_http_client, url_builder):
        """Password too short should explain the minimum length requirement."""
        response = await async_http_client.post(
            url_builder.url_for("register:register"),
            json={"username": "testuser", "email": "test@example.com", "password": "short"},
        )

        assert response.status_code == 422
        data = response.json()
        errors = _extract_validation_errors(data)
        assert len(errors) > 0, f"Expected validation errors, got: {data}"
        
        # Find the password error
        password_errors = [e for e in errors if "password" in e.get("loc", [])]
        assert len(password_errors) > 0
        
        # Verify the message is helpful (contains actual requirement, not just 'Value error')
        # The msg may have "Value error, " prefix, or ctx.error has clean message
        msg = password_errors[0].get("msg", "")
        ctx_error = password_errors[0].get("ctx", {}).get("error", "")
        full_msg = msg + ctx_error
        assert "12 characters" in full_msg or "at least" in full_msg, (
            f"Password error should explain minimum length, got: {msg}"
        )

    async def test_password_missing_uppercase_returns_helpful_message(self, async_http_client, url_builder):
        """Password without uppercase should explain the uppercase requirement."""
        response = await async_http_client.post(
            url_builder.url_for("register:register"),
            json={"username": "testuser", "email": "test@example.com", "password": "lowercaseonly123!"},
        )

        assert response.status_code == 422
        data = response.json()
        errors = _extract_validation_errors(data)
        assert len(errors) > 0
        
        password_errors = [e for e in errors if "password" in e.get("loc", [])]
        assert len(password_errors) > 0
        
        msg = password_errors[0].get("msg", "")
        assert "uppercase" in msg.lower(), f"Password error should mention uppercase requirement, got: {msg}"

    async def test_password_missing_special_char_returns_helpful_message(self, async_http_client, url_builder):
        """Password without special char should explain the special char requirement."""
        response = await async_http_client.post(
            url_builder.url_for("register:register"),
            json={"username": "testuser", "email": "test@example.com", "password": "NoSpecialChar123"},
        )

        assert response.status_code == 422
        data = response.json()
        errors = _extract_validation_errors(data)
        assert len(errors) > 0
        
        password_errors = [e for e in errors if "password" in e.get("loc", [])]
        assert len(password_errors) > 0
        
        msg = password_errors[0].get("msg", "")
        assert "special" in msg.lower(), f"Password error should mention special char requirement, got: {msg}"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    "route_or_path",
    [
        "mark_word_known",
        "bulk_mark_level",
        "filter_subtitles",
    ],
)
async def test_WhenEndpointsRequireMandatoryFields_ThenValidates(async_http_client, url_builder, route_or_path: str):
    """Invalid input: missing mandatory fields results in 422 validation errors."""
    helper = AsyncAuthHelper(async_http_client)
    _user, _token, headers = await helper.create_authenticated_user()

    # Determine endpoint - use url_builder for route names, hardcoded path otherwise
    endpoint = url_builder.url_for(route_or_path) if not route_or_path.startswith("/") else route_or_path

    response = await async_http_client.post(endpoint, json={}, headers=headers)

    assert response.status_code == 422
