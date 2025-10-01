"""Detailed vocabulary route behavior under protective testing."""

from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    return await AuthTestHelperAsync.register_and_login_async(async_client)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_known_can_unmarkCalled_ThenSucceeds(async_client):
    """Happy path: toggling known flag to False returns consistent structure."""
    flow = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"word": "sein", "known": False},
        headers=flow["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("known") is False
    assert body.get("word") == "sein"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_markCalled_ThenReturnscounts(async_client):
    """Happy path: bulk mark returns the number of affected words."""
    from services.vocabulary_preload_service import get_vocabulary_preload_service

    class FakeService:
        async def bulk_mark_level_known(self, user_id: int, level: str, known: bool, db=None):
            return 7

    # Override the dependency instead of monkeypatching
    fake_service = FakeService()
    async_client._transport.app.dependency_overrides[get_vocabulary_preload_service] = lambda: fake_service

    flow = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "A1", "known": True},
        headers=flow["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["word_count"] == 7
    assert body["level"] == "A1"

    # Clean up dependency override
    del async_client._transport.app.dependency_overrides[get_vocabulary_preload_service]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenstats_total_counts_include_levelsCalled_ThenSucceeds(async_client):
    """Boundary: stats aggregates totals from service-provided levels."""
    from services.vocabulary_preload_service import get_vocabulary_preload_service

    class FakeService:
        async def get_vocabulary_stats(self, db=None):
            return {"A1": {"total_words": 3}, "A2": {"total_words": 4}}

        async def get_user_known_words(self, user_id: int, level: str, db=None):
            return {"word1"}

    # Override the dependency instead of monkeypatching
    fake_service = FakeService()
    async_client._transport.app.dependency_overrides[get_vocabulary_preload_service] = lambda: fake_service

    flow = await _auth(async_client)

    response = await async_client.get("/api/vocabulary/library/stats", headers=flow["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_words"] == 7
    assert payload["total_known"] == 2

    # Clean up dependency override
    del async_client._transport.app.dependency_overrides[get_vocabulary_preload_service]
