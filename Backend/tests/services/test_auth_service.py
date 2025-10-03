"""Behavior-focused tests for `AuthService` following the 80/20 guidance."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from database.models import User
from services.authservice.auth_service import (
    AuthService,
    InvalidCredentialsError,
    SessionExpiredError,
    UserAlreadyExistsError,
)


@pytest.fixture
def db_session_mock():
    """Provide an async-capable session double that passes isinstance(AsyncSession) checks."""
    from sqlalchemy.ext.asyncio import AsyncSession

    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.add = Mock()
    session.begin_nested = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    return session


@pytest.fixture
def auth_service(db_session_mock: AsyncMock) -> AuthService:
    return AuthService(db_session_mock)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenUserRegistered_ThenCreatesRecordWithHashedPassword(auth_service, db_session_mock):
    """Happy path: registering a user inserts a new row with hashed password."""
    query_result = Mock()
    query_result.scalar_one_or_none.return_value = None
    db_session_mock.execute.return_value = query_result

    async def fake_refresh(user: User) -> None:
        user.id = 123
        user.created_at = datetime.utcnow()

    db_session_mock.refresh.side_effect = fake_refresh

    user = await auth_service.register_user("testuser", "Password123!")

    assert user.id == 123
    assert user.username == "testuser"
    db_session_mock.add.assert_called_once()
    db_session_mock.commit.assert_called_once()
    assert user.hashed_password != "Password123!"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenExistingUsernameRegistered_ThenRaisesUserAlreadyExistsError(auth_service, db_session_mock):
    """Invalid input: existing username raises `UserAlreadyExistsError`."""
    query_result = Mock()
    query_result.scalar_one_or_none.return_value = User(username="existing")
    db_session_mock.execute.return_value = query_result

    with pytest.raises(UserAlreadyExistsError):
        await auth_service.register_user("existing", "Password123!")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenValidCredentialsProvided_ThenReturnsAuthSession(auth_service, db_session_mock):
    """Happy path: login returns an AuthSession and records it in the DB."""
    stored_user = Mock()
    stored_user.id = 5
    stored_user.username = "user@example.com"
    stored_user.hashed_password = auth_service._hash_password("Password123!")
    stored_user.is_superuser = False
    stored_user.is_active = True
    stored_user.created_at = datetime.utcnow()
    stored_user.last_login = None

    query_result = Mock()
    query_result.scalar_one_or_none.return_value = stored_user
    db_session_mock.execute.return_value = query_result

    session = await auth_service.login("user@example.com", "Password123!")

    assert session.user.username == "user@example.com"
    assert session.session_token
    db_session_mock.add.assert_called()
    db_session_mock.commit.assert_called()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenInvalidCredentialsProvided_ThenRaisesInvalidCredentialsError(auth_service, db_session_mock):
    """Invalid input: unknown user triggers `InvalidCredentialsError`."""
    query_result = Mock()
    query_result.scalar_one_or_none.return_value = None
    db_session_mock.execute.return_value = query_result

    with pytest.raises(InvalidCredentialsError):
        await auth_service.login("missing", "Password123!")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenExpiredSessionValidated_ThenRaisesSessionExpiredError(auth_service, db_session_mock):
    """Boundary: expired session raises and signals deactivation."""
    session_row = Mock()
    session_row.session_token = "expired"
    session_row.expires_at = datetime.utcnow() - timedelta(minutes=1)
    session_row.is_active = True
    session_row.user_id = 1

    user_row = Mock()
    user_row.id = 1
    user_row.username = "user"

    query_result = Mock()
    query_result.first.return_value = (session_row, user_row)
    db_session_mock.execute.return_value = query_result

    with pytest.raises(SessionExpiredError):
        await auth_service.validate_session("expired")

    assert db_session_mock.execute.called


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLogoutCalled_ThenReturnsBooleanBasedOnRowsAffected(auth_service, db_session_mock):
    """Happy/boundary: logout returns True when a session was deactivated, otherwise False."""
    updated = AsyncMock()
    updated.rowcount = 1
    db_session_mock.execute.return_value = updated

    assert await auth_service.logout("token") is True

    updated.rowcount = 0
    assert await auth_service.logout("missing") is False


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenLanguagePreferencesUpdated_ThenReturnsTrue(auth_service, db_session_mock):
    """Boundary: until implemented, method returns True without DB mutations."""
    assert await auth_service.update_language_preferences(1, "en", "de") is True
    db_session_mock.execute.assert_not_called()
