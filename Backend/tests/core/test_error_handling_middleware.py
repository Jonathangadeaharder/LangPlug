"""
Tests for ErrorHandlingMiddleware branches by attaching it to a small FastAPI app.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

from core.exceptions import LangPlugException
from core.middleware import ErrorHandlingMiddleware
from services.authservice.auth_service import InvalidCredentialsError, SessionExpiredError, UserAlreadyExistsError


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenerror_handling_middleware_maps_exceptionsCalled_ThenSucceeds():
    app = FastAPI()

    @asynccontextmanager
    async def no_lifespan(_):
        yield

    app.router.lifespan_context = no_lifespan

    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/langplug")
    async def boom_langplug():
        raise LangPlugException("boom", status_code=418)

    @app.get("/invalid")
    async def boom_invalid():
        raise InvalidCredentialsError("bad")

    @app.get("/exists")
    async def boom_exists():
        raise UserAlreadyExistsError("exists")

    @app.get("/expired")
    async def boom_expired():
        raise SessionExpiredError("expired")

    @app.get("/generic")
    async def boom_generic():
        raise RuntimeError("x")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.get("/langplug")
        assert r.status_code == 418
        r = await client.get("/invalid")
        assert r.status_code == 401
        r = await client.get("/exists")
        assert r.status_code == 400
        r = await client.get("/expired")
        assert r.status_code == 401
        r = await client.get("/generic")
        assert r.status_code == 500
