"""
In-process tests to ensure vocabulary endpoints require Authorization.
"""
from __future__ import annotations

import pytest


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenvocabularyWithoutauth_stats_ThenReturnsError(async_client):
    r = await async_client.get("/api/vocabulary/library/stats")
    assert r.status_code == 401


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenvocabularyWithoutauth_level_ThenReturnsError(async_client):
    r = await async_client.get("/api/vocabulary/library/A1")
    assert r.status_code == 401


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenvocabularyWithoutauth_mark_known_ThenReturnsError(async_client):
    r = await async_client.post("/api/vocabulary/mark-known", json={"word": "sein", "known": True})
    assert r.status_code == 401
