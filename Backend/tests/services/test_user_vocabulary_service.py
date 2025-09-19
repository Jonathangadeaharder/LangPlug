"""Protective tests for `SQLiteUserVocabularyService`."""
from __future__ import annotations

import pytest

from services.dataservice.user_vocabulary_service import SQLiteUserVocabularyService


@pytest.fixture
def service() -> SQLiteUserVocabularyService:
    return SQLiteUserVocabularyService()


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenadd_known_words_persists_entriesCalled_ThenSucceeds(service):
    """Happy path: added words are returned on subsequent reads."""
    user_id = "user"
    words = {"hallo", "welt"}

    await service.add_known_words(user_id, words)

    known_words = await service.get_known_words(user_id)
    assert words.issubset(known_words)


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenis_word_known_handles_unknownCalled_ThenSucceeds(service):
    """Invalid path: querying unknown words returns False without raising."""
    result = await service.is_word_known("user", "missing")
    assert result is False


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenlearning_statistics_reports_countsCalled_ThenSucceeds(service):
    """Boundary: statistics reflect the number of stored words."""
    await service.add_known_words("user", {"eins", "zwei"})

    stats = await service.get_learning_statistics("user")

    assert stats["total_known"] >= 2


@pytest.mark.timeout(30)
@pytest.mark.anyio
async def test_Whenusers_are_isolatedCalled_ThenSucceeds(service):
    """Boundary: vocabularies are segregated by user id."""
    await service.add_known_words("alice", {"hello"})
    await service.add_known_words("bob", {"hola"})

    alice_words = await service.get_known_words("alice")
    bob_words = await service.get_known_words("bob")
    
    assert "hello" in alice_words
    assert "hello" not in bob_words
