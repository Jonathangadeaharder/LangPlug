"""
Unit tests for Pydantic serialization warnings detection.

These tests validate that our Pydantic models properly reject or warn about
invalid data structures, particularly the 'active' vs 'known' field issue.
"""

import warnings
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.models.processing import ProcessingStatus
from api.models.vocabulary import VocabularyWord


class TestVocabularyWordValidation:
    """Test VocabularyWord Pydantic validation with strict mode"""

    def test_vocabulary_word_with_known_field_succeeds(self):
        """Valid: VocabularyWord with 'known' field validates successfully"""
        valid_data = {"concept_id": str(uuid4()), "word": "Haus", "difficulty_level": "A1", "known": False}

        vocab_word = VocabularyWord(**valid_data)
        assert vocab_word.known is False
        assert vocab_word.word == "Haus"

    def test_vocabulary_word_with_active_field_fails_strict_mode(self):
        """Invalid: VocabularyWord with 'active' field should fail with extra='forbid'"""
        invalid_data = {
            "concept_id": str(uuid4()),
            "word": "Haus",
            "difficulty_level": "A1",
            "active": True,  # Wrong field - should be 'known'
        }

        # With extra="forbid", this should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWord(**invalid_data)

        # Verify the error mentions the forbidden field
        error_str = str(exc_info.value)
        assert "active" in error_str.lower() or "extra" in error_str.lower()

    def test_vocabulary_word_missing_required_fields_fails(self):
        """Invalid: VocabularyWord missing required fields should fail"""
        invalid_data = {
            "concept_id": str(uuid4()),
            # Missing 'word' (required)
            # Missing 'difficulty_level' (required)
            "known": False,
        }

        with pytest.raises(ValidationError) as exc_info:
            VocabularyWord(**invalid_data)

        error_str = str(exc_info.value)
        assert "word" in error_str.lower() or "difficulty_level" in error_str.lower()

    def test_vocabulary_word_invalid_difficulty_level_fails(self):
        """Invalid: VocabularyWord with invalid difficulty level should fail"""
        invalid_data = {
            "concept_id": str(uuid4()),
            "word": "Haus",
            "difficulty_level": "Z9",  # Invalid CEFR level
            "known": False,
        }

        with pytest.raises(ValidationError) as exc_info:
            VocabularyWord(**invalid_data)

        error_str = str(exc_info.value)
        assert "difficulty_level" in error_str.lower()

    def test_vocabulary_word_all_fields_succeeds(self):
        """Valid: VocabularyWord with all fields validates successfully"""
        complete_data = {
            "concept_id": str(uuid4()),
            "word": "Haus",
            "translation": "house",
            "lemma": "haus",
            "difficulty_level": "A1",
            "semantic_category": "noun",
            "domain": "housing",
            "gender": "das",
            "plural_form": "Häuser",
            "pronunciation": "haʊs",
            "notes": "Neuter noun",
            "known": True,
        }

        vocab_word = VocabularyWord(**complete_data)
        assert vocab_word.word == "Haus"
        assert vocab_word.known is True
        assert vocab_word.gender == "das"


class TestProcessingStatusWithVocabulary:
    """Test ProcessingStatus validation with vocabulary field"""

    def test_processing_status_with_valid_vocabulary_succeeds(self):
        """Valid: ProcessingStatus with properly structured vocabulary"""
        vocab_words = [
            {
                "concept_id": str(uuid4()),
                "word": "gehen",
                "difficulty_level": "A1",
                "translation": "to go",
                "lemma": "gehen",
                "known": False,
            },
            {
                "concept_id": str(uuid4()),
                "word": "Haus",
                "difficulty_level": "A1",
                "translation": "house",
                "lemma": "haus",
                "known": True,
            },
        ]

        status_data = {
            "status": "completed",
            "progress": 100.0,
            "current_step": "Processing complete",
            "message": "Vocabulary extracted",
            "vocabulary": vocab_words,
        }

        status = ProcessingStatus(**status_data)
        assert status.status == "completed"
        assert status.vocabulary is not None
        assert len(status.vocabulary) == 2

        # Verify each vocabulary word is a valid VocabularyWord
        for vocab_word in status.vocabulary:
            assert isinstance(vocab_word, VocabularyWord)
            assert hasattr(vocab_word, "known")
            assert vocab_word.known in [True, False]

    def test_processing_status_with_invalid_vocabulary_fails(self):
        """Invalid: ProcessingStatus with vocabulary containing 'active' field should fail"""
        vocab_words_with_active = [
            {
                "concept_id": str(uuid4()),
                "word": "gehen",
                "difficulty_level": "A1",
                "active": True,  # Wrong field - should cause validation error
            }
        ]

        status_data = {
            "status": "completed",
            "progress": 100.0,
            "current_step": "Processing complete",
            "vocabulary": vocab_words_with_active,
        }

        # This should fail because VocabularyWord has extra="forbid"
        with pytest.raises(ValidationError) as exc_info:
            ProcessingStatus(**status_data)

        error_str = str(exc_info.value)
        # Error should mention either 'active' or 'extra fields'
        assert "active" in error_str.lower() or "extra" in error_str.lower()

    def test_processing_status_assignment_validates(self):
        """Test that validate_assignment=True catches issues on field assignment"""
        status = ProcessingStatus(status="processing", progress=50.0, current_step="Processing...")

        # Valid assignment should work
        valid_vocab = [VocabularyWord(concept_id=uuid4(), word="Test", difficulty_level="A1", known=False)]
        status.vocabulary = valid_vocab
        assert len(status.vocabulary) == 1

        # Invalid assignment should fail with validate_assignment=True
        invalid_vocab_dict = [
            {
                "concept_id": str(uuid4()),
                "word": "Test",
                "difficulty_level": "A1",
                "active": True,  # Wrong field
            }
        ]

        with pytest.raises(ValidationError):
            status.vocabulary = invalid_vocab_dict


class TestPydanticWarningsDetection:
    """Test detection of Pydantic serialization warnings"""

    def test_no_warnings_with_correct_structure(self):
        """No warnings should be raised for correct vocabulary structure"""
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            # Create vocabulary with correct structure
            vocab = VocabularyWord(
                concept_id=uuid4(),
                word="lernen",
                difficulty_level="A2",
                translation="to learn",
                lemma="lernen",
                known=False,
            )

            # Serialize to dict
            vocab.model_dump()

            # Create ProcessingStatus with this vocabulary
            status = ProcessingStatus(status="completed", progress=100.0, current_step="Complete", vocabulary=[vocab])

            # Serialize status to JSON
            status.model_dump_json()

        # Filter for Pydantic warnings
        pydantic_warnings = [
            w
            for w in warning_list
            if "pydantic" in str(w.category).lower() or "serialization" in str(w.message).lower()
        ]

        assert len(pydantic_warnings) == 0, (
            f"Expected no Pydantic warnings, but got {len(pydantic_warnings)}:\n"
            + "\n".join(str(w.message) for w in pydantic_warnings)
        )

    def test_vocabulary_filter_service_output_validates(self):
        """Test that VocabularyFilterService._create_vocabulary_word_dict produces valid structure"""
        from unittest.mock import Mock

        from services.processing.chunk_services.vocabulary_filter_service import VocabularyFilterService

        service = VocabularyFilterService()

        mock_word = Mock(word="Buch", lemma="buch", difficulty_level="A1", translation="book", part_of_speech="noun")

        # Get the dict created by the service
        vocab_dict = service._create_vocabulary_word_dict(mock_word)

        # Verify structure
        assert "known" in vocab_dict, "Should have 'known' field"
        assert "active" not in vocab_dict, "Should NOT have 'active' field"

        # Verify it can be validated by Pydantic
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            vocab_word = VocabularyWord(**vocab_dict)

            assert vocab_word.known is False
            assert vocab_word.word == "Buch"

        # Check for Pydantic warnings
        pydantic_warnings = [
            w
            for w in warning_list
            if "pydantic" in str(w.category).lower() or "serialization" in str(w.message).lower()
        ]

        assert len(pydantic_warnings) == 0, (
            f"VocabularyFilterService output should not trigger Pydantic warnings. "
            f"Got {len(pydantic_warnings)} warnings:\n" + "\n".join(str(w.message) for w in pydantic_warnings)
        )


class TestRegressionPrevention:
    """Regression tests to prevent the 'active' field bug from returning"""

    def test_vocabulary_dict_with_active_field_is_rejected(self):
        """
        Regression test: Ensure dicts with 'active' field are rejected.

        This was the original bug - VocabularyFilterService returned dicts
        with 'active': True instead of 'known': False.
        """
        # Simulate the old buggy structure
        buggy_vocab_dict = {
            "concept_id": str(uuid4()),
            "word": "glücklich",
            "difficulty_level": "C2",
            "translation": "happy",
            "lemma": "glücklich",
            "active": True,  # Old bug: should be 'known'
        }

        # With extra="forbid", this should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWord(**buggy_vocab_dict)

        error_message = str(exc_info.value)
        assert (
            "active" in error_message.lower() or "extra" in error_message.lower()
        ), "ValidationError should mention the 'active' field or extra fields"

    def test_processing_status_with_buggy_vocabulary_is_rejected(self):
        """
        Regression test: ProcessingStatus with buggy vocabulary should fail validation.

        This ensures the API cannot return malformed vocabulary to clients.
        """
        buggy_vocab_list = [
            {
                "concept_id": str(uuid4()),
                "word": "test",
                "difficulty_level": "A1",
                "active": True,  # Bug: wrong field
            }
        ]

        status_data = {
            "status": "completed",
            "progress": 100.0,
            "current_step": "Complete",
            "vocabulary": buggy_vocab_list,
        }

        # Should fail validation
        with pytest.raises(ValidationError):
            ProcessingStatus(**status_data)

    def test_vocabulary_service_creates_correct_field_name(self):
        """
        Direct test: Verify VocabularyFilterService uses 'known' not 'active'.
        """
        from unittest.mock import Mock

        from services.processing.chunk_services.vocabulary_filter_service import VocabularyFilterService

        service = VocabularyFilterService()
        mock_word = Mock(word="Test", lemma="test", difficulty_level="A1", translation=None, part_of_speech=None)

        result_dict = service._create_vocabulary_word_dict(mock_word)

        # Critical assertion: 'known' field must exist
        assert "known" in result_dict, "VocabularyFilterService MUST create 'known' field, not 'active'"

        # Critical assertion: 'active' field must NOT exist
        assert "active" not in result_dict, "VocabularyFilterService must NOT create 'active' field (regression bug)"

        # Verify default value
        assert result_dict["known"] is False, "'known' field should default to False"
