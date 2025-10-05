"""Integration checks for vocabulary endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenmark_known_endpointCalled_ThenSucceeds(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    concept_id = str(uuid4())

    response = await async_client.post(
        "/api/vocabulary/mark-known",
        json={"concept_id": concept_id, "known": True},
        headers=flow["headers"],
    )

    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlibrary_levelWithoutvalid_code_ThenReturnsError(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.get(
        "/api/vocabulary/library/Z9", params={"target_language": "de"}, headers=flow["headers"]
    )

    # Invalid level parameter should return 422 (validation error)
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for invalid level), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvocabulary_stats_endpointCalled_ThenReturnsMultilingualStats(async_client):
    """Integration test for multilingual vocabulary stats endpoint."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.get(
        "/api/vocabulary/stats",
        params={"target_language": "de", "translation_language": "es"},
        headers=flow["headers"],
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "levels" in payload
    assert "target_language" in payload
    assert "total_words" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlanguages_endpointCalled_ThenReturnsLanguageList(async_client):
    """Integration test for supported languages endpoint."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.get(
        "/api/vocabulary/languages",
        headers=flow["headers"],
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "languages" in payload
    assert isinstance(payload["languages"], list)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_mark_endpointCalled_ThenSucceedsWithLanguage(async_client):
    """Integration test for multilingual bulk mark endpoint."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "A1", "target_language": "de", "known": True},
        headers=flow["headers"],
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()
    assert "success" in payload
    assert "level" in payload
    assert "word_count" in payload
