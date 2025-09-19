"""Targeted behavior tests for `UserRepository`."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from unittest.mock import Mock

import pytest

from services.repository.user_repository import User, UserRepository


@pytest.fixture
def connection_double():
    conn = Mock()
    conn.cursor.return_value = Mock()
    return conn


@pytest.fixture
def repository(connection_double, monkeypatch):
    repo = UserRepository()

    @contextmanager
    def fake_connection():
        yield connection_double

    repo.get_connection = fake_connection  # type: ignore[assignment]
    repo.transaction = fake_connection  # type: ignore[assignment]
    return repo


@pytest.fixture
def user_row() -> dict[str, str]:
    return {
        "id": 1,
        "username": "tester",
        "hashed_password": "hash",
        "email": "tester@example.com",
        "native_language": "en",
        "target_language": "de",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.mark.timeout(30)
def test_Whenfind_by_usernameCalled_ThenReturnsuser(repository, connection_double, user_row):
    """Happy path: repository maps DB rows into the domain model."""
    cursor = connection_double.cursor.return_value
    cursor.fetchone.return_value = user_row

    user = repository.find_by_username("tester")

    assert isinstance(user, User)
    assert user.username == "tester"
    cursor.execute.assert_called_once_with("SELECT * FROM users WHERE username = ?", ("tester",))


@pytest.mark.timeout(30)
def test_Whenfind_by_username_missingCalled_ThenReturnsnone(repository, connection_double):
    """Invalid input: missing row returns `None` without raising."""
    connection_double.cursor.return_value.fetchone.return_value = None

    assert repository.find_by_username("missing") is None


@pytest.mark.timeout(30)
def test_Whenupdate_language_preferenceCalled_ThenUpdatesrow(repository, connection_double):
    """Happy/boundary: language update returns True when rows were affected."""
    cursor = connection_double.cursor.return_value
    cursor.rowcount = 1

    assert repository.update_language_preference(1, "en", "es") is True

    cursor.rowcount = 0
    assert repository.update_language_preference(1, "en", "es") is False


@pytest.mark.timeout(30)
def test_Whenemail_exists_checks_with_optional_exclusionCalled_ThenSucceeds(repository, connection_double):
    """Boundary: `email_exists` supports exclusion IDs for uniqueness checks."""
    cursor = connection_double.cursor.return_value
    cursor.fetchone.return_value = (1,)
    assert repository.email_exists("tester@example.com") is True
    cursor.execute.assert_any_call("SELECT COUNT(*) FROM users WHERE email = ?", ("tester@example.com",))

    cursor.fetchone.return_value = (0,)
    assert repository.email_exists("tester@example.com", exclude_id=2) is False
    cursor.execute.assert_any_call(
        "SELECT COUNT(*) FROM users WHERE email = ? AND id != ?",
        ("tester@example.com", 2),
    )
