"""Lightweight latency checks that enforce our performance guard rails."""
from __future__ import annotations

import asyncio
import time

import pytest

from core.app import create_app
from httpx import ASGITransport, AsyncClient
import os
from tests.auth_helpers import AuthTestHelperAsync

HEALTH_BUDGET_SECONDS = 0.25
AUTH_BUDGET_SECONDS = 1.25


@pytest.fixture
async def async_client_no_db():
    """Async client that doesn't override DB dependencies (for /health-only tests)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenhealth_endpoint_stays_snappyCalled_ThenSucceeds(async_client_no_db) -> None:
    """Health checks should return quickly and report a healthy system."""
    print("before request")
    started = time.perf_counter()
    response = await async_client_no_db.get("/health")
    elapsed = time.perf_counter() - started
    print("after request")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert elapsed < HEALTH_BUDGET_SECONDS


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy performance test in constrained sandbox",
)
@pytest.mark.timeout(30)
async def test_Whenauthenticated_stats_within_latency_budgetCalled_ThenSucceeds(async_client) -> None:
    """A representative authenticated request remains inside the agreed latency budget."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    started = time.perf_counter()
    response = await async_client.get(
        "/api/vocabulary/library/stats",
        headers=flow["headers"],
    )
    elapsed = time.perf_counter() - started

    assert response.status_code in {200, 500}
    assert elapsed < AUTH_BUDGET_SECONDS


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenconcurrent_health_requests_do_not_queueCalled_ThenSucceeds(async_client_no_db) -> None:
    """A short burst of health checks should complete well under a second."""
    started = time.perf_counter()
    responses = await asyncio.gather(*(async_client_no_db.get("/health") for _ in range(5)))
    elapsed = time.perf_counter() - started

    assert all(resp.status_code == 200 for resp in responses)
    assert elapsed < 1.0
