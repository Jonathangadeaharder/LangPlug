"""Assertion helpers to keep test bodies concise and follow CLAUDE.md rules."""
from __future__ import annotations

from typing import Any, Dict


def assert_successful_response(response, expected_codes: set[int] = {200}) -> None:
    """Assert response has successful status code."""
    assert response.status_code in expected_codes


def assert_json_response(response) -> None:
    """Assert response is JSON format."""
    assert "application/json" in response.headers.get("content-type", "")


def assert_validation_error_response(response, field_name: str = None) -> None:
    """Assert response is a 422 validation error, optionally for specific field."""
    assert response.status_code == 422
    if field_name:
        response_data = response.json()
        if "detail" in response_data:
            # Standard FastAPI validation error format
            errors = response_data["detail"]
            assert any(err["loc"][-1] == field_name for err in errors)
        elif "error" in response_data and "details" in response_data["error"]:
            # Custom validation error format
            errors = response_data["error"]["details"]
            assert any(err["loc"][-1] == field_name for err in errors)


def assert_auth_error_response(response) -> None:
    """Assert response is a 401 authentication error."""
    assert response.status_code == 401
    assert "application/json" in response.headers.get("content-type", "")


def assert_task_response(response) -> None:
    """Assert response contains task-related fields for async operations."""
    assert response.status_code in {200, 202}
    body = response.json()
    assert "task" in body or "task_id" in body or "status" in body


def assert_json_error_response(response, expected_status: int) -> None:
    """Assert response is JSON error with specific status code."""
    assert response.status_code == expected_status
    assert "application/json" in response.headers.get("content-type", "")
    response_data = response.json()
    # Handle both FastAPI standard format and custom error format
    assert "detail" in response_data or ("error" in response_data and "message" in response_data["error"])


def assert_dict_response(response, expected_codes: set[int] = {200}) -> None:
    """Assert response has expected status and returns dict."""
    assert response.status_code in expected_codes
    assert isinstance(response.json(), dict)
