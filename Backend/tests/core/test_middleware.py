"""
Tests for middleware setup: CORS headers and LangPlugException handler.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.exceptions import LangPlugException
from core.middleware import setup_middleware


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whencors_and_exception_handlerCalled_ThenSucceeds():
    app = FastAPI()

    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    app.router.lifespan_context = no_lifespan

    # Add CORS middleware explicitly for this test since setup_middleware no longer includes it
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_middleware(app)

    @app.get("/boom")
    async def boom():
        raise LangPlugException("boom", status_code=418)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Preflight request should be handled by CORS middleware
        r_options = await client.options(
            "/boom",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r_options.status_code in (200, 204)
        assert r_options.headers.get("access-control-allow-origin") is not None

        r = await client.get("/boom", headers={"Origin": "http://localhost:3000"})
        assert r.status_code == 418
        data = r.json()
        assert data.get("detail") == "boom"
        assert data.get("type") in ("LangPlugException", "ConfigurationError", "ProcessingError")
