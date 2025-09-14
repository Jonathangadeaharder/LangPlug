"""
Additional error-path coverage for auth routes: generic register/login failures.
"""
from __future__ import annotations

import httpx
import pytest
from contextlib import asynccontextmanager

from core.app import create_app
from core.dependencies import get_auth_service, get_database_manager


class BoomAuth:
    def register_user(self, username: str, password: str):
        raise Exception("some other error")

    def login(self, username: str, password: str):
        raise Exception("boom")


@pytest.mark.anyio
async def test_register_generic_error_returns_500(async_client):
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_):
        yield
    app.router.lifespan_context = no_lifespan

    # share db from main app if available
    try:
        shared_db = async_client._transport.app.dependency_overrides[get_database_manager]()
    except Exception:
        shared_db = None
    if shared_db is not None:
        app.dependency_overrides[get_database_manager] = lambda: shared_db
    app.dependency_overrides[get_auth_service] = lambda: BoomAuth()

    transport = httpx.ASGITransport(app=app)
    client2 = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        # Send valid data that will pass Pydantic validation but trigger service error
        r = await client2.post("/api/auth/register", json={"username": "testuser", "password": "TestPass123!"})
        assert r.status_code == 500
    finally:
        await client2.aclose()


@pytest.mark.anyio
async def test_login_generic_error_returns_500(async_client):
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_):
        yield
    app.router.lifespan_context = no_lifespan

    try:
        shared_db = async_client._transport.app.dependency_overrides[get_database_manager]()
    except Exception:
        shared_db = None
    if shared_db is not None:
        app.dependency_overrides[get_database_manager] = lambda: shared_db
    app.dependency_overrides[get_auth_service] = lambda: BoomAuth()

    transport = httpx.ASGITransport(app=app)
    client2 = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        # Send valid data that will pass Pydantic validation but trigger service error
        r = await client2.post("/api/auth/login", json={"username": "testuser", "password": "TestPass123!"})
        assert r.status_code == 500
    finally:
        await client2.aclose()


@pytest.mark.anyio
async def test_register_validation_error_returns_400(async_client):
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_):
        yield
    app.router.lifespan_context = no_lifespan

    class ValAuth:
        def register_user(self, u, p, email=None):
            raise Exception("password must be at least 8 characters")

    try:
        shared_db = async_client._transport.app.dependency_overrides[get_database_manager]()
    except Exception:
        shared_db = None
    if shared_db is not None:
        app.dependency_overrides[get_database_manager] = lambda: shared_db
    app.dependency_overrides[get_auth_service] = lambda: ValAuth()

    transport = httpx.ASGITransport(app=app)
    client2 = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        # Send valid data that will pass Pydantic validation but trigger service validation error
        r = await client2.post("/api/auth/register", json={"username": "validuser", "password": "ValidPass123!"})
        assert r.status_code == 400
    finally:
        await client2.aclose()
