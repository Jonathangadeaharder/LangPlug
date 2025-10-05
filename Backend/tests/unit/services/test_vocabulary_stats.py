"""Tests for stats-facing helpers on VocabularyService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.vocabulary.vocabulary_service import VocabularyService


@pytest.fixture
def service_with_stats(monkeypatch) -> VocabularyService:
    monkeypatch.setenv("TESTING", "1")
    service = VocabularyService()
    return service


@pytest.mark.asyncio
async def test_get_supported_languages_delegates_to_stats(service_with_stats: VocabularyService) -> None:
    expected = [
        {"code": "en", "name": "English"},
        {"code": "de", "name": "German"},
    ]
    stats_mock = MagicMock()
    stats_mock.get_supported_languages = AsyncMock(return_value=expected)
    service_with_stats.stats_service = stats_mock

    result = await service_with_stats.get_supported_languages()

    assert result == expected
    stats_mock.get_supported_languages.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_vocabulary_stats_passes_through_arguments(service_with_stats: VocabularyService) -> None:
    stats_mock = MagicMock()
    stats_mock.get_vocabulary_stats = AsyncMock(return_value={"total_words": 10})
    service_with_stats.stats_service = stats_mock

    result = await service_with_stats.get_vocabulary_stats(language="de", include_levels=True)

    assert result == {"total_words": 10}
    stats_mock.get_vocabulary_stats.assert_awaited_once_with(language="de", include_levels=True)


@pytest.mark.asyncio
async def test_get_user_progress_summary_delegates_to_stats(service_with_stats: VocabularyService) -> None:
    stats_mock = MagicMock()
    stats_mock.get_user_progress_summary = AsyncMock(return_value={"known": 5})
    service_with_stats.stats_service = stats_mock

    summary = await service_with_stats.get_user_progress_summary(db_session=None, user_id="abc")

    assert summary == {"known": 5}
    stats_mock.get_user_progress_summary.assert_awaited_once_with(None, "abc")
