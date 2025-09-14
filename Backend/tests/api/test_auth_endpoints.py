"""
In-process API tests for auth endpoints using FastAPI TestClient and dependency overrides.
Removes external localhost dependency and speeds up feedback.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

import pytest


class _User:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username
        self.is_admin = False
        self.is_active = True
        self.created_at = datetime.utcnow().isoformat()
        self.last_login = None


class _Session:
    def __init__(self, token: str, user: _User):
        self.session_token = token
        self.user = user
        self.expires_at = datetime.utcnow() + timedelta(hours=1)


class FakeAuthService:
    """Minimal in-memory auth service for API tests."""
    def __init__(self) -> None:
        self._users: Dict[str, _User] = {}
        self._next_id = 1
        self._tokens: Dict[str, _User] = {}

    # Methods used by routes
    def register_user(self, username: str, password: str, email: str | None = None) -> _User:
        if username in self._users:
            raise ValueError("User already exists")
        user = _User(self._next_id, username)
        self._next_id += 1
        self._users[username] = user
        return user

    def login(self, username: str, password: str) -> _Session:
        if username not in self._users:
            # auto-register for convenience in test
            self.register_user(username, password)
        user = self._users[username]
        user.last_login = datetime.utcnow().isoformat()
        token = f"testtoken-{user.id}-{username}"
        self._tokens[token] = user
        return _Session(token, user)

    def logout(self, token: str) -> bool:
        return self._tokens.pop(token, None) is not None

    # Used by get_current_user (not directly in these tests)
    def validate_session(self, token: str) -> _User:
        user = self._tokens.get(token)
        if not user:
            raise ValueError("Invalid token")
        return user


# Uses shared client fixture from conftest.py


import pytest


@pytest.mark.anyio
async def test_register_endpoint(async_client):
    payload = {"username": "testuser_api", "password": "TestPass123"}
    resp = await async_client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == payload["username"]
    assert isinstance(data["id"], int)
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_login_endpoint(async_client):
    # ensure user exists
    await async_client.post("/api/auth/register", json={"username": "admin", "password": "AdminPass123"})

    resp = await async_client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data and data["token"].startswith("testtoken-")
    assert data["user"]["username"] == "admin"


@pytest.mark.anyio
async def test_register_duplicate_username(async_client):
    payload = {"username": "dupuser", "password": "TestPass123"}
    r1 = await async_client.post("/api/auth/register", json=payload)
    assert r1.status_code == 200
    r2 = await async_client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
