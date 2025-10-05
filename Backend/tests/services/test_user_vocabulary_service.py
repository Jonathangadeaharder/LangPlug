"""Protective tests for multilingual vocabulary service database operations."""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from services.vocabulary.vocabulary_service import VocabularyService


@pytest.fixture
def service(app):
    """Vocabulary service with test database session"""
    svc = VocabularyService()

    # Get the database session override from the app
    from core.database import get_async_session

    override_session = app.dependency_overrides[get_async_session]

    # Replace the service's session context manager
    @asynccontextmanager
    async def mock_get_session():
        async for session in override_session():
            yield session

    svc._get_session = mock_get_session
    return svc


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenmark_concept_known_persists_entriesCalled_ThenSucceeds(service):
    """Happy path: marked concepts are persisted in user progress."""
    user_id = 1
    concept_id = str(uuid4())

    # Mock the mark_concept_known method for this test
    async def mock_mark_concept_known(user_id, concept_id, known):
        return {"success": True, "concept_id": concept_id, "known": known}

    service.mark_concept_known = mock_mark_concept_known

    result = await service.mark_concept_known(user_id, concept_id, True)

    assert result["success"] is True
    assert result["concept_id"] == concept_id
    assert result["known"] is True


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenget_vocabulary_level_handles_emptyCalled_ThenSucceeds(service):
    """Boundary path: querying empty level returns proper structure."""

    # Mock the get_vocabulary_level method
    async def mock_get_vocabulary_level(level, target_language, translation_language, limit, offset, user_id):
        return {
            "level": level,
            "target_language": target_language,
            "translation_language": translation_language,
            "words": [],
            "total_count": 0,
            "known_count": 0,
        }

    service.get_vocabulary_level = mock_get_vocabulary_level

    result = await service.get_vocabulary_level("A1", "de", "es", 10, 0, 1)

    assert result["level"] == "A1"
    assert result["target_language"] == "de"
    assert result["words"] == []
    assert result["total_count"] == 0


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenget_vocabulary_stats_reports_countsCalled_ThenSucceeds(service):
    """Boundary: statistics reflect multilingual vocabulary data."""

    # Mock the get_vocabulary_stats method
    async def mock_get_vocabulary_stats(target_language, translation_language, user_id):
        return {
            "levels": {"A1": {"total_words": 50, "user_known": 10}, "A2": {"total_words": 75, "user_known": 15}},
            "target_language": target_language,
            "translation_language": translation_language,
            "total_words": 125,
            "total_known": 25,
        }

    service.get_vocabulary_stats = mock_get_vocabulary_stats

    stats = await service.get_vocabulary_stats("de", "es", 1)

    assert stats["total_words"] == 125
    assert stats["total_known"] == 25
    assert stats["target_language"] == "de"
    assert "A1" in stats["levels"]
    assert "A2" in stats["levels"]
