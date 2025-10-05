"""
Integration test for vocabulary serialization in chunk processing API flow.

This test validates that the complete data flow from VocabularyFilterService
through ChunkProcessingService to API response serialization produces valid
Pydantic models without serialization warnings.

Tests the fix for: Pydantic serialization warnings about 'active' field
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import ValidationError

from api.models.processing import ProcessingStatus
from api.models.vocabulary import VocabularyWord
from core.config import settings
from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.skip(
    reason="TODO: Update for refactored architecture - DirectSubtitleProcessor no longer in VocabularyFilterService"
)
@pytest.mark.anyio
@pytest.mark.timeout(60)
async def test_chunk_processing_vocabulary_serialization_valid(async_http_client, monkeypatch, tmp_path, caplog):
    """
    Integration test: Chunk processing returns vocabulary that matches Pydantic schema.

    This test validates the complete flow:
    1. POST /api/process/chunk - Start chunk processing
    2. GET /api/process/progress/{task_id} - Poll for completion
    3. Verify ProcessingStatus.vocabulary contains valid VocabularyWord objects
    4. Ensure no Pydantic serialization warnings occur

    Catches the bug where VocabularyFilterService returned dicts with 'active' field
    instead of 'known' field, causing Pydantic serialization warnings.
    """
    caplog.set_level(logging.WARNING)

    # Setup authentication
    auth = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    # Create test video and subtitle files
    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        video_path = tmp_path / "test_episode.mp4"
        video_path.write_bytes(b"fake video data")

        subtitle_path = tmp_path / "test_episode.srt"
        subtitle_content = """1
00:00:00,000 --> 00:00:05,000
Hallo, wie geht es dir?

2
00:00:05,000 --> 00:00:10,000
Das ist ein schöner Tag heute.

3
00:00:10,000 --> 00:00:15,000
Ich gehe jetzt zum Supermarkt einkaufen.
"""
        subtitle_path.write_text(subtitle_content, encoding="utf-8")

        # Mock transcription service to avoid actual audio processing
        mock_transcription = Mock(is_initialized=True)
        mock_transcription.transcribe.return_value = Mock(segments=[])
        monkeypatch.setattr("core.dependencies.get_transcription_service", lambda: mock_transcription)

        # Mock subtitle processor to return vocabulary with proper structure
        mock_filter_result = {
            "blocking_words": [
                # Simulate actual FilteredWord objects from DirectSubtitleProcessor
                Mock(word="gehen", lemma="gehen", difficulty_level="A1", translation="to go", part_of_speech="verb"),
                Mock(
                    word="Supermarkt",
                    lemma="supermarkt",
                    difficulty_level="A2",
                    translation="supermarket",
                    part_of_speech="noun",
                ),
                Mock(
                    word="einkaufen",
                    lemma="einkaufen",
                    difficulty_level="B1",
                    translation="to shop",
                    part_of_speech="verb",
                ),
            ],
            "learning_subtitles": [],
            "statistics": {"total_words": 10, "blocking_words": 3},
        }

        mock_processor = Mock()
        mock_processor.process_srt_file = AsyncMock(return_value=mock_filter_result)

        monkeypatch.setattr(
            "services.processing.chunk_services.vocabulary_filter_service.DirectSubtitleProcessor",
            lambda: mock_processor,
        )

        # Step 1: Start chunk processing
        response = await async_http_client.post(
            "/api/process/chunk",
            json={"video_path": video_path.name, "start_time": 0.0, "end_time": 15.0},
            headers=auth["headers"],
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        task_data = response.json()
        assert "task_id" in task_data, "Response should contain task_id"
        task_id = task_data["task_id"]

        # Step 2: Poll for completion (with timeout)
        max_polls = 30
        poll_interval = 0.5
        completed = False
        final_status = None

        for _ in range(max_polls):
            await asyncio.sleep(poll_interval)

            progress_response = await async_http_client.get(f"/api/process/progress/{task_id}", headers=auth["headers"])

            assert (
                progress_response.status_code == 200
            ), f"Progress check failed: {progress_response.status_code}: {progress_response.text}"

            status_data = progress_response.json()

            # Validate response matches ProcessingStatus schema
            status = ProcessingStatus(**status_data)

            if status.status == "completed":
                completed = True
                final_status = status
                break
            elif status.status == "error":
                pytest.fail(f"Chunk processing failed: {status.message}")

        assert completed, f"Chunk processing did not complete within {max_polls * poll_interval} seconds"
        assert final_status is not None, "Final status should not be None"

        # Step 3: Validate vocabulary structure
        assert hasattr(final_status, "vocabulary"), "Completed status should have vocabulary"
        assert final_status.vocabulary is not None, "Vocabulary should not be None"
        assert len(final_status.vocabulary) > 0, "Vocabulary should contain words"

        # Step 4: Validate each vocabulary word matches Pydantic schema
        for vocab_word in final_status.vocabulary:
            # This will raise ValidationError if structure doesn't match
            validated_word = VocabularyWord(**vocab_word)

            # Verify required fields are present
            assert validated_word.word is not None, "Word should not be None"
            assert validated_word.difficulty_level in [
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
            ], f"Invalid difficulty level: {validated_word.difficulty_level}"

            # Verify 'known' field exists (not 'active')
            assert hasattr(validated_word, "known"), "VocabularyWord should have 'known' field"
            assert isinstance(validated_word.known, bool), "known field should be boolean"

            # Verify 'active' field does NOT exist (old bug)
            vocab_dict = vocab_word if isinstance(vocab_word, dict) else vocab_word.model_dump()
            assert "active" not in vocab_dict, (
                f"Vocabulary word should not have 'active' field (old bug). "
                f"Word: {validated_word.word}, Fields: {vocab_dict.keys()}"
            )

            # Verify concept_id is valid UUID
            assert validated_word.concept_id is not None, "concept_id should not be None"
            # UUID validation happens in Pydantic, if we get here it's valid

        # Step 5: Check for Pydantic serialization warnings
        pydantic_warnings = [
            record
            for record in caplog.records
            if "PydanticSerializationUnexpectedValue" in record.message
            or "serialized value may not be as expected" in record.message
        ]

        assert len(pydantic_warnings) == 0, (
            f"Found {len(pydantic_warnings)} Pydantic serialization warnings:\n"
            + "\n".join(record.message for record in pydantic_warnings)
        )

        # Additional validation: Ensure vocabulary can be serialized to JSON without issues
        try:
            json_vocab = json.dumps(
                [word.model_dump() if hasattr(word, "model_dump") else word for word in final_status.vocabulary],
                default=str,  # Handle UUID serialization
            )
            assert len(json_vocab) > 0, "Serialized vocabulary should not be empty"
        except Exception as e:
            pytest.fail(f"Failed to serialize vocabulary to JSON: {e}")


@pytest.mark.anyio
async def test_vocabulary_word_schema_validation():
    """
    Unit-level test: Verify VocabularyWord Pydantic model rejects 'active' field.

    This test ensures the Pydantic model itself enforces the correct schema.
    """
    from uuid import uuid4

    # Valid vocabulary word with 'known' field
    valid_word = {
        "concept_id": str(uuid4()),
        "word": "Haus",
        "difficulty_level": "A1",
        "known": False,  # Correct field
    }

    # Should validate successfully
    vocab_word = VocabularyWord(**valid_word)
    assert vocab_word.known is False
    assert hasattr(vocab_word, "known")

    # Invalid vocabulary word with 'active' field instead of 'known'
    invalid_word = {
        "concept_id": str(uuid4()),
        "word": "Haus",
        "difficulty_level": "A1",
        "active": True,  # Wrong field (old bug)
    }

    # With extra="forbid", this should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        VocabularyWord(**invalid_word)

    # Verify the error mentions the forbidden field
    error_str = str(exc_info.value)
    assert "active" in error_str.lower() or "extra" in error_str.lower()


@pytest.mark.anyio
async def test_vocabulary_filter_service_creates_correct_structure():
    """
    Unit test: Verify VocabularyFilterService creates dicts with 'known' field.

    This test directly validates the fix in vocabulary_filter_service.py:110
    """
    from services.processing.chunk_services.vocabulary_filter_service import VocabularyFilterService

    service = VocabularyFilterService()

    # Create dict with string values (service accepts dict input)
    mock_word = {
        "word": "lernen",
        "lemma": "lernen",
        "difficulty_level": "A2",
        "translation": "to learn",
        "part_of_speech": "verb",
    }

    # Call the method that was fixed
    vocab_dict = service._create_vocabulary_word_dict(mock_word)

    # Verify structure
    assert "known" in vocab_dict, "Vocabulary dict should have 'known' field"
    assert vocab_dict["known"] is False, "known field should default to False"
    assert "active" not in vocab_dict, "Vocabulary dict should NOT have 'active' field (old bug)"

    # Verify it can be used to create a valid Pydantic model
    vocab_word = VocabularyWord(**vocab_dict)
    assert vocab_word.known is False
    assert vocab_word.word == "lernen"
    assert vocab_word.difficulty_level == "A2"
