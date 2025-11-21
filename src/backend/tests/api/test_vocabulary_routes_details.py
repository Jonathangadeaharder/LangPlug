"""Detailed vocabulary route behavior under protective testing."""

from __future__ import annotations

import pytest

from tests.helpers import AsyncAuthHelper


async def _auth(async_client):
    helper = AsyncAuthHelper(async_client)
    return await helper.create_authenticated_user()


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenmark_known_can_unmarkCalled_ThenSucceeds(async_client, url_builder, seeded_vocabulary):
    """Happy path: toggling known flag to False returns consistent structure."""
    _user, _token, headers = await _auth(async_client)

    # Get a real vocabulary word from the library (seeded_vocabulary fixture ensures data exists)
    library_response = await async_client.get(
        url_builder.url_for("get_vocabulary_level", level="A1"),
        params={"target_language": "de", "limit": 1},
        headers=headers,
    )
    assert library_response.status_code == 200, f"Failed to get vocabulary: {library_response.text}"
    words = library_response.json()["words"]

    # Fail fast if no words - this indicates a seeding failure
    assert len(words) > 0, "No vocabulary words found - seeding failed or vocabulary system is broken"

    # Use the first word's lemma
    word_lemma = words[0]["lemma"]

    response = await async_client.post(
        url_builder.url_for("mark_word_known"),
        json={"lemma": word_lemma, "language": "de", "known": False},
        headers=headers,
    )

    assert response.status_code == 200, f"Failed to mark word as unknown: {response.text}"
    body = response.json()
    assert body.get("known") is False
    assert body.get("lemma") == word_lemma


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenbulk_markCalled_ThenReturnscounts(async_client, url_builder, app):
    """Happy path: bulk mark returns the number of affected words."""
    from unittest.mock import AsyncMock

    from core.dependencies import get_vocabulary_service
    from services.vocabulary.vocabulary_service import VocabularyService

    # Create mock service with mocked progress_service
    mock_service = VocabularyService()
    mock_bulk_mark = AsyncMock(return_value={"updated_count": 7})
    mock_service.progress_service.bulk_mark_level = mock_bulk_mark

    _user, _token, headers = await _auth(async_client)

    # Override dependency injection
    app.dependency_overrides[get_vocabulary_service] = lambda: mock_service
    try:
        response = await async_client.post(
            url_builder.url_for("bulk_mark_level"),
            json={"level": "A1", "known": True, "target_language": "de"},
            headers=headers,
        )
    finally:
        # Clean up override
        del app.dependency_overrides[get_vocabulary_service]

    assert response.status_code == 200
    body = response.json()
    assert body["word_count"] == 7
    assert body["level"] == "A1"
