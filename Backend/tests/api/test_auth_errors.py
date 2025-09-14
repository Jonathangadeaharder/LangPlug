"""
Error-path tests for auth endpoints using isolated app + overrides.
"""
from __future__ import annotations

import pytest
import httpx
from contextlib import asynccontextmanager

from core.app import create_app
from core.dependencies import get_auth_service, get_database_manager


class FailAuth:
    def login(self, username: str, password: str):
        raise Exception("Invalid username or password")


@pytest.mark.anyio
async def test_login_invalid_credentials_returns_401(async_client):
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_app):
        yield
    app.router.lifespan_context = no_lifespan

    # Reuse same db manager as the shared app when available
    try:
        shared_db = async_client._transport.app.dependency_overrides[get_database_manager]()
    except Exception:
        shared_db = None

    if shared_db is not None:
        app.dependency_overrides[get_database_manager] = lambda: shared_db
    app.dependency_overrides[get_auth_service] = lambda: FailAuth()

    transport = httpx.ASGITransport(app=app)
    client2 = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        r = await client2.post("/api/auth/login", json={"username": "x", "password": "y"})
        assert r.status_code == 401
    finally:
        await client2.aclose()

