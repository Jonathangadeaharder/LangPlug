"""Tests for progress-oriented helpers on VocabularyService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.vocabulary.vocabulary_service import VocabularyService


@pytest.fixture
def service_with_progress(monkeypatch) -> VocabularyService:
    monkeypatch.setenv("TESTING", "1")
    service = VocabularyService()
    return service


@pytest.mark.asyncio
async def test_mark_word_known_delegates_to_progress(service_with_progress: VocabularyService) -> None:
    progress_mock = MagicMock()
    progress_mock.mark_word_known = AsyncMock(return_value={"success": True})
    service_with_progress.progress_service = progress_mock

    db_session = object()
    result = await service_with_progress.mark_word_known(1, "Hund", "de", True, db_session)

    assert result == {"success": True}
    progress_mock.mark_word_known.assert_awaited_once_with(1, "Hund", "de", True, db_session)


@pytest.mark.asyncio
async def test_bulk_mark_level_delegates_to_progress(service_with_progress: VocabularyService) -> None:
    progress_mock = MagicMock()
    progress_mock.bulk_mark_level = AsyncMock(return_value={"updated_count": 3})
    service_with_progress.progress_service = progress_mock

    db_session = object()
    result = await service_with_progress.bulk_mark_level(db_session, 7, "de", "A1", False)

    assert result == {"updated_count": 3}
    progress_mock.bulk_mark_level.assert_awaited_once_with(db_session, 7, "de", "A1", False)


@pytest.mark.asyncio
async def test_get_user_vocabulary_stats_delegates_to_progress(service_with_progress: VocabularyService) -> None:
    progress_mock = MagicMock()
    progress_mock.get_user_vocabulary_stats = AsyncMock(return_value={"total_known": 4})
    service_with_progress.progress_service = progress_mock

    db_session = object()
    stats = await service_with_progress.get_user_vocabulary_stats(5, "de", db_session)

    assert stats == {"total_known": 4}
    progress_mock.get_user_vocabulary_stats.assert_awaited_once_with(5, "de", db_session)
