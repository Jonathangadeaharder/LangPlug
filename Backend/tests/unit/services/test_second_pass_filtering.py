"""
Test second-pass filtering functionality
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from services.processing.filtering_handler import FilteringHandler
from sqlalchemy.dialects import sqlite
from services.filterservice.interface import FilteredSubtitle, FilteredWord, FilteringResult, WordStatus
from api.models.processing import VocabularyWord


@pytest.fixture
def mock_subtitle_processor():
    """Create a mock subtitle processor"""
    processor = AsyncMock()
    return processor


@pytest.fixture
def filtering_handler(mock_subtitle_processor):
    """Create a FilteringHandler with mocked dependencies"""
    handler = FilteringHandler(subtitle_processor=mock_subtitle_processor)
    return handler


@pytest.fixture(autouse=True)
def stub_lemmatizer(monkeypatch):
    """Avoid loading spaCy during unit tests by stubbing lemma resolution."""
    monkeypatch.setattr(
        "services.nlp.lemma_resolver.lemmatize_word",
        lambda text, language: text.lower(),
    )


@pytest.fixture
def sample_subtitles():
    """Create sample filtered subtitles for testing"""
    return [
        FilteredSubtitle(
            original_text="Der Mann ist fett",
            start_time=0.0,
            end_time=2.0,
            words=[
                FilteredWord("der", 0.0, 0.5, WordStatus.ACTIVE),
                FilteredWord("mann", 0.5, 1.0, WordStatus.ACTIVE),
                FilteredWord("ist", 1.0, 1.5, WordStatus.ACTIVE),
                FilteredWord("fett", 1.5, 2.0, WordStatus.ACTIVE, metadata={"is_blocker": True})
            ]
        ),
        FilteredSubtitle(
            original_text="Das Haus ist groß",
            start_time=2.0,
            end_time=4.0,
            words=[
                FilteredWord("das", 2.0, 2.5, WordStatus.ACTIVE),
                FilteredWord("haus", 2.5, 3.0, WordStatus.ACTIVE, metadata={"is_blocker": True}),
                FilteredWord("ist", 3.0, 3.5, WordStatus.ACTIVE),
                FilteredWord("groß", 3.5, 4.0, WordStatus.ACTIVE)
            ]
        ),
        FilteredSubtitle(
            original_text="Ich bin hier",
            start_time=4.0,
            end_time=6.0,
            words=[
                FilteredWord("ich", 4.0, 4.5, WordStatus.ACTIVE),
                FilteredWord("bin", 4.5, 5.0, WordStatus.ACTIVE),
                FilteredWord("hier", 5.0, 6.0, WordStatus.ACTIVE)
            ]
        )
    ]


@pytest.fixture
def sample_filtering_result(sample_subtitles):
    """Create a sample filtering result with blocker words"""
    blocker_words = [
        FilteredWord("fett", 1.5, 2.0, WordStatus.ACTIVE, metadata={"difficulty_level": "B1"}),
        FilteredWord("haus", 2.5, 3.0, WordStatus.ACTIVE, metadata={"difficulty_level": "A2"}),
    ]

    return FilteringResult(
        learning_subtitles=sample_subtitles,
        blocker_words=blocker_words,
        empty_subtitles=[],
        statistics={"total_words": 11, "blocker_count": 2}
    )


@pytest.mark.asyncio
async def test_refilter_with_no_known_words(filtering_handler, mock_subtitle_processor, sample_filtering_result):
    """Test refiltering when no words are marked as known"""
    # Mock the coordinator's refilter method
    expected_result = {
        "total_subtitles": 3,
        "translation_count": 2,
        "needs_translation": [0, 1],
        "filtering_stats": {
            "total_blockers": 2,
            "known_blockers": 0,
            "unknown_blockers": 2
        }
    }

    with patch.object(filtering_handler.coordinator, 'refilter_for_translations', new_callable=AsyncMock) as mock_refilter:
        mock_refilter.return_value = expected_result

        # Call refilter with empty known words list
        result = await filtering_handler.refilter_for_translations(
            srt_path="/tmp/test.srt",
            user_id="1",
            known_words=[],
            user_level="A1",
            target_language="de"
        )

    # All subtitles with blockers should need translation (indices 0 and 1)
    assert result["total_subtitles"] == 3
    assert result["translation_count"] == 2
    assert result["needs_translation"] == [0, 1]
    assert result["filtering_stats"]["total_blockers"] == 2
    assert result["filtering_stats"]["known_blockers"] == 0
    assert result["filtering_stats"]["unknown_blockers"] == 2


@pytest.mark.asyncio
async def test_refilter_with_one_known_word(filtering_handler, mock_subtitle_processor, sample_filtering_result):
    """Test refiltering when one blocker word is marked as known"""
    # Mock the coordinator's refilter method
    expected_result = {
        "total_subtitles": 3,
        "translation_count": 1,
        "needs_translation": [1],
        "filtering_stats": {
            "total_blockers": 2,
            "known_blockers": 1,
            "unknown_blockers": 1
        }
    }

    with patch.object(filtering_handler.coordinator, 'refilter_for_translations', new_callable=AsyncMock) as mock_refilter:
        mock_refilter.return_value = expected_result

        # Mark "fett" as known
        result = await filtering_handler.refilter_for_translations(
            srt_path="/tmp/test.srt",
            user_id="1",
            known_words=["fett"],
            user_level="A1",
            target_language="de"
        )

    # Only subtitle with "haus" blocker should need translation (index 1)
    assert result["total_subtitles"] == 3
    assert result["translation_count"] == 1
    assert result["needs_translation"] == [1]
    assert result["filtering_stats"]["total_blockers"] == 2
    assert result["filtering_stats"]["known_blockers"] == 1
    assert result["filtering_stats"]["unknown_blockers"] == 1


@pytest.mark.asyncio
async def test_refilter_with_all_blockers_known(filtering_handler, mock_subtitle_processor, sample_filtering_result):
    """Test refiltering when all blocker words are marked as known"""
    # Mock the coordinator's refilter method
    expected_result = {
        "total_subtitles": 3,
        "translation_count": 0,
        "needs_translation": [],
        "filtering_stats": {
            "total_blockers": 2,
            "known_blockers": 2,
            "unknown_blockers": 0
        }
    }

    with patch.object(filtering_handler.coordinator, 'refilter_for_translations', new_callable=AsyncMock) as mock_refilter:
        mock_refilter.return_value = expected_result

        # Mark both "fett" and "haus" as known
        result = await filtering_handler.refilter_for_translations(
            srt_path="/tmp/test.srt",
            user_id="1",
            known_words=["fett", "haus"],
            user_level="A1",
            target_language="de"
        )

    # No subtitles should need translation
    assert result["total_subtitles"] == 3
    assert result["translation_count"] == 0
    assert result["needs_translation"] == []
    assert result["filtering_stats"]["total_blockers"] == 2
    assert result["filtering_stats"]["known_blockers"] == 2
    assert result["filtering_stats"]["unknown_blockers"] == 0


@pytest.mark.asyncio
async def test_refilter_case_insensitive(filtering_handler, mock_subtitle_processor, sample_filtering_result):
    """Test that refiltering is case-insensitive for word matching"""
    # Mock the coordinator's refilter method
    expected_result = {
        "total_subtitles": 3,
        "translation_count": 1,
        "needs_translation": [1],
        "filtering_stats": {
            "total_blockers": 2,
            "known_blockers": 1,
            "unknown_blockers": 1
        }
    }

    with patch.object(filtering_handler.coordinator, 'refilter_for_translations', new_callable=AsyncMock) as mock_refilter:
        mock_refilter.return_value = expected_result

        # Mark "FETT" as known (uppercase)
        result = await filtering_handler.refilter_for_translations(
            srt_path="/tmp/test.srt",
            user_id="1",
            known_words=["FETT"],  # Uppercase
            user_level="A1",
            target_language="de"
        )

    # Should still recognize "fett" as known
    assert result["translation_count"] == 1
    assert result["needs_translation"] == [1]
    assert result["filtering_stats"]["known_blockers"] == 1


@pytest.mark.asyncio
async def test_extract_blocking_words(filtering_handler, mock_subtitle_processor):
    """Test extracting blocking words from subtitles"""
    # Mock the coordinator's extract_blocking_words method
    fake_vocab = [
        VocabularyWord(
            concept_id=uuid.uuid4(),
            word="schwierig",
            translation="",
            difficulty_level="B2",
            known=False
        ),
        VocabularyWord(
            concept_id=uuid.uuid4(),
            word="kompliziert",
            translation="",
            difficulty_level="C1",
            known=False
        ),
    ]

    with patch.object(filtering_handler.coordinator, 'extract_blocking_words', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = fake_vocab

        # Extract blocking words
        vocab_words = await filtering_handler.extract_blocking_words(
            srt_path="/tmp/test.srt",
            user_id="1",
            user_level="A1"
        )

    # Check extracted vocabulary words
    assert len(vocab_words) == 2
    assert vocab_words[0].word == "schwierig"
    assert vocab_words[0].difficulty_level == "B2"
    assert vocab_words[0].known is False
    assert vocab_words[1].word == "kompliziert"
    assert vocab_words[1].difficulty_level == "C1"
    assert vocab_words[1].known is False

    # Check that concept_ids are preserved
    assert all(isinstance(word.concept_id, uuid.UUID) for word in vocab_words)


@pytest.mark.asyncio
async def test_build_vocabulary_words_german_heuristics(filtering_handler, monkeypatch):
    """Test that vocabulary building works with German heuristics (via facade)"""
    # This test previously tested a private method _build_vocabulary_words
    # which now lives in VocabularyBuilderService. Testing via the facade:

    dummy_concept_id = uuid.uuid4()
    expected_vocab = [
        VocabularyWord(
            concept_id=dummy_concept_id,
            word="fetter",
            translation="",
            difficulty_level="B1",
            known=False
        )
    ]

    # Mock the coordinator's extract_blocking_words which uses the vocab builder
    with patch.object(filtering_handler.coordinator, 'extract_blocking_words', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = expected_vocab

        vocab_words = await filtering_handler.extract_blocking_words(
            srt_path="/tmp/test.srt",
            user_id="1",
            user_level="A1"
        )

    assert vocab_words
    assert vocab_words[0].word == "fetter"
    assert vocab_words[0].concept_id == dummy_concept_id
