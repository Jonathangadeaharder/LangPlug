"""Auth model validation tests focused on custom logic."""

import pytest
from pydantic import ValidationError

from api.models.auth import AuthResponse, RegisterRequest, UserResponse


@pytest.mark.parametrize(
    "password, expected_error",
    [
        ("weakpass1", "Password must contain at least one uppercase letter"),
        ("WEAKPASS1", "Password must contain at least one lowercase letter"),
        ("Weakpass", "Password must contain at least one digit"),
    ],
)
def test_register_request_rejects_password_without_required_character(password: str, expected_error: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(username="testuser", password=password)

    assert expected_error in str(exc_info.value)


def test_register_request_accepts_strong_password() -> None:
    request = RegisterRequest(username="testuser", password="ValidPass123!")

    assert request.username == "testuser"
    assert request.password == "ValidPass123!"


def test_auth_response_includes_nested_user_model() -> None:
    user_data = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_superuser": False,
        "is_active": True,
        "created_at": "2024-01-15T10:30:00Z",
        "last_login": None,
    }

    response = AuthResponse(token="jwt_token_here", user=UserResponse(**user_data), expires_at="2024-01-21T14:45:00Z")

    assert response.token == "jwt_token_here"
    assert response.user.email == "test@example.com"
