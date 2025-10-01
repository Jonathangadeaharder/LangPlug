"""Improved assertion helpers that follow test standards and provide clear error messages."""

from __future__ import annotations

import json
from typing import Any


def assert_status_code(response, expected_code: int, context: str = "") -> None:
    """Assert response has exact expected status code with clear error message."""
    actual_code = response.status_code
    if actual_code != expected_code:
        error_msg = f"Expected status {expected_code}, got {actual_code}"
        if context:
            error_msg = f"{context}: {error_msg}"

        # Include response body in error for debugging
        try:
            response_body = response.text[:500]  # First 500 chars
            error_msg += f"\nResponse: {response_body}"
        except Exception:
            error_msg += "\n(Could not read response body)"

        raise AssertionError(error_msg)


def assert_json_response(response, expected_code: int = 200) -> dict[str, Any]:
    """Assert response is JSON with expected status and return parsed data."""
    assert_status_code(response, expected_code)

    content_type = response.headers.get("content-type", "")
    assert "application/json" in content_type, f"Expected JSON response, got {content_type}"

    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON response: {e}")


def assert_success_response(response, expected_code: int = 200) -> dict[str, Any]:
    """Assert successful response and return JSON data."""
    return assert_json_response(response, expected_code)


def assert_validation_error(response, field_name: str | None = None) -> dict[str, Any]:
    """Assert response is 422 validation error, optionally checking specific field."""
    data = assert_json_response(response, 422)

    if field_name:
        # Check FastAPI validation error format
        if "detail" in data and isinstance(data["detail"], list):
            field_errors = [
                err
                for err in data["detail"]
                if isinstance(err, dict) and isinstance(err.get("loc"), list) and err["loc"][-1] == field_name
            ]
            assert field_errors, f"No validation error found for field '{field_name}'"
        else:
            raise AssertionError(f"Unexpected validation error format: {data}")

    return data


def assert_authentication_error(response) -> dict[str, Any]:
    """Assert response is 401 authentication error."""
    return assert_json_response(response, 401)


def assert_authorization_error(response) -> dict[str, Any]:
    """Assert response is 403 authorization error."""
    return assert_json_response(response, 403)


def assert_not_found_error(response) -> dict[str, Any]:
    """Assert response is 404 not found error."""
    return assert_json_response(response, 404)


def assert_server_error(response) -> dict[str, Any]:
    """Assert response is 500 server error - use sparingly and only when expected."""
    return assert_json_response(response, 500)


def assert_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """Assert that all required fields are present in response data."""
    missing_fields = [field for field in required_fields if field not in data]
    assert not missing_fields, f"Missing required fields: {missing_fields}"


def assert_field_types(data: dict[str, Any], field_types: dict[str, type]) -> None:
    """Assert that fields have expected types."""
    type_errors = []
    for field, expected_type in field_types.items():
        if field in data:
            actual_type = type(data[field])
            if not isinstance(data[field], expected_type):
                type_errors.append(f"{field}: expected {expected_type.__name__}, got {actual_type.__name__}")

    assert not type_errors, f"Type validation errors: {type_errors}"


def assert_response_structure(
    response,
    expected_code: int = 200,
    required_fields: list[str] | None = None,
    field_types: dict[str, type] | None = None,
    optional_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Comprehensive response structure validation."""
    data = assert_json_response(response, expected_code)

    if required_fields:
        assert_required_fields(data, required_fields)

    if field_types:
        assert_field_types(data, field_types)

    return data


def assert_list_response(
    response,
    expected_code: int = 200,
    min_length: int | None = None,
    max_length: int | None = None,
    item_structure: dict[str, type] | None = None,
) -> list[dict[str, Any]]:
    """Assert response contains a list with optional validation."""
    data = assert_json_response(response, expected_code)

    assert isinstance(data, list), f"Expected list response, got {type(data).__name__}"

    if min_length is not None:
        assert len(data) >= min_length, f"Expected at least {min_length} items, got {len(data)}"

    if max_length is not None:
        assert len(data) <= max_length, f"Expected at most {max_length} items, got {len(data)}"

    if item_structure and data:
        # Validate structure of first item as sample
        assert_field_types(data[0], item_structure)

    return data


def assert_vocabulary_response_structure(data: dict[str, Any]) -> None:
    """Assert vocabulary API response has expected structure."""
    required_fields = ["level", "target_language", "words", "total_count", "known_count"]
    field_types = {"level": str, "target_language": str, "words": list, "total_count": int, "known_count": int}

    assert_required_fields(data, required_fields)
    assert_field_types(data, field_types)

    # Validate word structure if words present
    if data["words"]:
        word = data["words"][0]
        word_required_fields = ["concept_id", "word"]
        word_field_types = {"concept_id": str, "word": str}
        assert_required_fields(word, word_required_fields)
        assert_field_types(word, word_field_types)


def assert_auth_response_structure(data: dict[str, Any]) -> None:
    """Assert authentication response has expected structure."""
    required_fields = ["access_token", "token_type"]
    field_types = {"access_token": str, "token_type": str}

    assert_required_fields(data, required_fields)
    assert_field_types(data, field_types)


def assert_user_response_structure(data: dict[str, Any]) -> None:
    """Assert user response has expected structure."""
    required_fields = ["id", "username", "is_active"]
    field_types = {
        "id": (str, int),  # Could be string or int depending on implementation
        "username": str,
        "is_active": bool,
    }

    assert_required_fields(data, required_fields)

    # Handle multiple allowed types
    for field, allowed_types in field_types.items():
        if field in data:
            if isinstance(allowed_types, tuple):
                assert isinstance(
                    data[field], allowed_types
                ), f"Field {field}: expected one of {[t.__name__ for t in allowed_types]}, got {type(data[field]).__name__}"
            else:
                assert isinstance(
                    data[field], allowed_types
                ), f"Field {field}: expected {allowed_types.__name__}, got {type(data[field]).__name__}"


def assert_error_response_structure(data: dict[str, Any]) -> None:
    """Assert error response has expected structure."""
    # Support both FastAPI standard format and custom formats
    has_detail = "detail" in data
    has_error_message = "error" in data and isinstance(data["error"], dict) and "message" in data["error"]

    assert (
        has_detail or has_error_message
    ), f"Expected error response to have 'detail' or 'error.message', got keys: {list(data.keys())}"


# Performance assertion helpers
def assert_response_time(response, max_seconds: float) -> None:
    """Assert response time is within acceptable limits."""
    if hasattr(response, "elapsed"):
        elapsed = response.elapsed.total_seconds()
        assert elapsed <= max_seconds, f"Response took {elapsed:.3f}s, expected ≤ {max_seconds}s"


# Test-specific assertion helpers
def assert_pagination_response(
    data: dict[str, Any], expected_page: int | None = None, expected_per_page: int | None = None
) -> None:
    """Assert paginated response has expected structure."""
    required_fields = ["items", "total", "page", "per_page", "pages"]
    field_types = {"items": list, "total": int, "page": int, "per_page": int, "pages": int}

    assert_required_fields(data, required_fields)
    assert_field_types(data, field_types)

    if expected_page is not None:
        assert data["page"] == expected_page, f"Expected page {expected_page}, got {data['page']}"

    if expected_per_page is not None:
        assert data["per_page"] == expected_per_page, f"Expected per_page {expected_per_page}, got {data['per_page']}"


def assert_health_response(data: dict[str, Any]) -> None:
    """Assert health check response has expected structure."""
    required_fields = ["status"]
    field_types = {"status": str}

    assert_required_fields(data, required_fields)
    assert_field_types(data, field_types)
    assert data["status"] in ["healthy", "unhealthy"], f"Invalid health status: {data['status']}"


# Context managers for assertion groups
class AssertionContext:
    """Context manager for grouping related assertions with better error messages."""

    def __init__(self, context: str):
        self.context = context
        self.errors: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.errors:
            error_msg = f"\n{self.context} assertions failed:\n" + "\n".join(f"  - {error}" for error in self.errors)
            raise AssertionError(error_msg)

    def assert_that(self, condition: bool, message: str) -> None:
        """Add assertion to context."""
        if not condition:
            self.errors.append(message)


# Usage examples:
# with AssertionContext("User registration validation"):
#     ctx.assert_that(response.status_code == 201, "Registration should return 201")
#     ctx.assert_that("id" in data, "Response should include user ID")
#     ctx.assert_that(data["is_active"] == True, "New users should be active")
