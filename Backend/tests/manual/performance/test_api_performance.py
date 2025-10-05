"""Lightweight latency checks that enforce our performance guard rails."""

from __future__ import annotations

import asyncio
import os
import time

import pytest
from httpx import ASGITransport, AsyncClient

from core.app import create_app
from tests.helpers import AuthTestHelperAsync

HEALTH_BUDGET_SECONDS = 0.25
AUTH_BUDGET_SECONDS = 1.25
VOCAB_STATS_BUDGET_SECONDS = 5.0  # Vocabulary stats can be slower due to database queries


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
    started = time.perf_counter()
    response = await async_client_no_db.get("/health")
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert elapsed < HEALTH_BUDGET_SECONDS, f"Health check took {elapsed:.3f}s (budget: {HEALTH_BUDGET_SECONDS}s)"


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy performance test in constrained sandbox",
)
@pytest.mark.timeout(30)
async def test_Whenmultilingual_vocab_stats_within_latency_budgetCalled_ThenSucceeds(async_client) -> None:
    """Multilingual vocabulary stats request remains inside the agreed latency budget."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    started = time.perf_counter()
    response = await async_client.get(
        "/api/vocabulary/stats",
        params={"target_language": "de", "translation_language": "es"},
        headers=flow["headers"],
    )
    elapsed = time.perf_counter() - started

    # Performance test: validate both correctness and timing
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert elapsed < VOCAB_STATS_BUDGET_SECONDS


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy performance test in constrained sandbox",
)
@pytest.mark.timeout(30)
async def test_Whenvocab_level_query_within_budgetCalled_ThenSucceeds(async_client) -> None:
    """Vocabulary level query with multilingual parameters stays performant."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    started = time.perf_counter()
    response = await async_client.get(
        "/api/vocabulary/library/A1",
        params={"target_language": "de", "translation_language": "es", "limit": 50},
        headers=flow["headers"],
    )
    elapsed = time.perf_counter() - started

    # Performance test: validate both correctness and timing
    # Should return 200 with valid test data - no 422 hedging allowed
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Verify we get expected payload structure for performance test
    data = response.json()
    assert "words" in data
    assert "level" in data
    assert data["level"] == "A1"

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
