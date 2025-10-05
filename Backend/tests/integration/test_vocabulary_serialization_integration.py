"""
Unit tests for vocabulary serialization and Pydantic model validation.

Tests the fix for: Pydantic serialization warnings about 'active' field.

These tests ensure:
1. VocabularyWord Pydantic model rejects 'active' field (old bug)
2. VocabularyFilterService creates dicts with correct 'known' field
"""

import pytest
from pydantic import ValidationError

from api.models.vocabulary import VocabularyWord


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
