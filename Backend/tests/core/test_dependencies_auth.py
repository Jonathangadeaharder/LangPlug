"""
Tests for core.dependencies authentication helpers: WebSocket authentication and backward compatibility.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from core import dependencies as deps
from database.models import User


class MockJWTAuth:
    def __init__(self, user=None, should_fail=False):
        self.user = user
        self.should_fail = should_fail

    async def authenticate(self, token: str, db):
        if self.should_fail:
            raise Exception("Authentication failed")
        return self.user


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenget_current_user_ws_successCalled_ThenSucceeds(monkeypatch):
    """Test WebSocket authentication with valid token"""
    mock_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="fake_hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )

    mock_jwt_auth = MockJWTAuth(user=mock_user)
    monkeypatch.setattr("core.auth.jwt_authentication", mock_jwt_auth)

    # Create a mock db session
    mock_db = AsyncMock()

    user = await deps.get_current_user_ws("valid_token", mock_db)
    assert user.username == "testuser"
    assert user.email == "test@example.com"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_get_current_user_ws_InvalidToken(monkeypatch):
    """Test WebSocket authentication with invalid token"""
    mock_jwt_auth = MockJWTAuth(user=None, should_fail=False)
    monkeypatch.setattr("core.auth.jwt_authentication", mock_jwt_auth)

    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await deps.get_current_user_ws("invalid_token", mock_db)

    assert exc_info.value.status_code == 401
    assert "Invalid authentication" in exc_info.value.detail


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenget_current_user_ws_auth_exceptionCalled_ThenSucceeds(monkeypatch):
    """Test WebSocket authentication when authentication throws exception"""
    mock_jwt_auth = MockJWTAuth(should_fail=True)
    monkeypatch.setattr("core.auth.jwt_authentication", mock_jwt_auth)

    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await deps.get_current_user_ws("token", mock_db)

    assert exc_info.value.status_code == 401
    assert "Invalid authentication" in exc_info.value.detail


def test_Whenget_auth_service_backward_compatibilityCalled_ThenSucceeds():
    """Test that get_auth_service returns a FastAPI-Users instance for backward compatibility"""
    auth_service = deps.get_auth_service()
    # Just verify it returns something (for backward compatibility with tests)
    assert auth_service is not None


def test_Whenget_database_manager_backward_compatibilityCalled_ThenSucceeds():
    """Test that get_database_manager returns the database engine"""
    db_manager = deps.get_database_manager()
    # Just verify it returns the engine
    assert db_manager is not None
