"""
Comprehensive tests for VocabularyDTO validation and security
Testing input validation, SQL injection prevention, and field constraints
"""

import pytest
from pydantic import ValidationError

from api.dtos.vocabulary_dto import (
    UserProgressDTO,
    VocabularyLibraryDTO,
    VocabularySearchDTO,
    VocabularyStatsDTO,
    VocabularyWordDTO,
)


class TestVocabularyWordDTOValidation:
    """Test VocabularyWordDTO field validation"""

    def test_When_valid_vocabulary_word_data_Then_dto_created(self):
        """Test valid vocabulary word data creates DTO successfully"""
        # Arrange & Act
        dto = VocabularyWordDTO(
            id=1,
            word="Hallo",
            lemma="hallo",
            difficulty_level="A1",
            language="de",
            part_of_speech="interjection",
            frequency=100,
            example_sentence="Hallo, wie geht es dir?",
            definition="A greeting",
            is_known=False,
        )

        # Assert
        assert dto.word == "Hallo"
        assert dto.lemma == "hallo"
        assert dto.difficulty_level == "A1"
        assert dto.language == "de"

    def test_When_word_empty_string_Then_validation_error(self):
        """Test empty word string is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(word="", difficulty_level="A1", language="de")

        assert "word" in str(exc_info.value)

    def test_When_word_too_long_Then_validation_error(self):
        """Test word exceeding max length is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(
                word="a" * 201,  # Exceeds 200 character limit
                difficulty_level="A1",
                language="de",
            )

        assert "word" in str(exc_info.value)

    def test_When_word_contains_invalid_characters_Then_validation_error(self):
        """Test word with invalid characters is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(word="test<script>alert('xss')</script>", difficulty_level="A1", language="de")

        assert "Word contains invalid characters" in str(exc_info.value)

    def test_When_word_contains_sql_characters_Then_validation_error(self):
        """Test word with SQL injection attempts is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(word="test'; DROP TABLE vocabulary; --", difficulty_level="A1", language="de")

        assert "Word contains invalid characters" in str(exc_info.value)

    def test_When_word_contains_special_chars_Then_validation_error(self):
        """Test word with special characters is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(word="test@#$%^&*()", difficulty_level="A1", language="de")

        assert "Word contains invalid characters" in str(exc_info.value)

    def test_When_word_contains_valid_unicode_Then_accepted(self):
        """Test word with valid Unicode characters is accepted"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="Café", difficulty_level="A1", language="fr")

        # Assert
        assert dto.word == "Café"

    def test_When_word_contains_german_umlauts_Then_accepted(self):
        """Test word with German umlauts is accepted"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="Mädchen", difficulty_level="A1", language="de")

        # Assert
        assert dto.word == "Mädchen"

    def test_When_word_contains_hyphen_Then_accepted(self):
        """Test word with hyphen is accepted"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="self-study", difficulty_level="B1", language="en")

        # Assert
        assert dto.word == "self-study"

    def test_When_word_contains_apostrophe_Then_accepted(self):
        """Test word with apostrophe is accepted"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="l'eau", difficulty_level="A1", language="fr")

        # Assert
        assert dto.word == "l'eau"

    def test_When_word_has_leading_trailing_spaces_Then_trimmed(self):
        """Test word with leading/trailing spaces is trimmed"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="  test  ", difficulty_level="A1", language="en")

        # Assert
        assert dto.word == "test"


class TestVocabularyWordDTODifficultyValidation:
    """Test difficulty level validation"""

    @pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2", "unknown"])
    def test_When_valid_difficulty_level_Then_accepted(self, level):
        """Test all valid difficulty levels are accepted"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="test", difficulty_level=level, language="en")

        # Assert
        assert dto.difficulty_level == level

    def test_When_invalid_difficulty_level_Then_validation_error(self):
        """Test invalid difficulty level is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(
                word="test",
                difficulty_level="D1",  # Invalid level
                language="en",
            )

        assert "Invalid difficulty level" in str(exc_info.value)
        assert "A1" in str(exc_info.value)  # Error message includes valid options


class TestVocabularyWordDTOLanguageValidation:
    """Test language code validation"""

    @pytest.mark.parametrize("lang", ["de", "en", "es", "fr", "it", "pt", "ru", "zh", "ja", "ko"])
    def test_When_valid_language_code_Then_accepted(self, lang):
        """Test all valid language codes are accepted"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="test", difficulty_level="A1", language=lang)

        # Assert
        assert dto.language == lang.lower()

    def test_When_invalid_language_code_Then_validation_error(self):
        """Test invalid language code is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(
                word="test",
                difficulty_level="A1",
                language="xx",  # Invalid language code
            )

        assert "Invalid language code" in str(exc_info.value)
        assert "de" in str(exc_info.value)  # Error message includes valid options

    def test_When_language_code_uppercase_Then_converted_to_lowercase(self):
        """Test language code is converted to lowercase"""
        # Arrange & Act
        dto = VocabularyWordDTO(word="test", difficulty_level="A1", language="DE")

        # Assert
        assert dto.language == "de"


class TestVocabularyWordDTOOptionalFields:
    """Test optional field validation"""

    def test_When_frequency_negative_Then_validation_error(self):
        """Test negative frequency is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(word="test", difficulty_level="A1", language="en", frequency=-1)

        assert "frequency" in str(exc_info.value)

    def test_When_example_sentence_too_long_Then_validation_error(self):
        """Test example sentence exceeding max length is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(
                word="test",
                difficulty_level="A1",
                language="en",
                example_sentence="a" * 1001,  # Exceeds 1000 character limit
            )

        assert "example_sentence" in str(exc_info.value)

    def test_When_definition_too_long_Then_validation_error(self):
        """Test definition exceeding max length is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(
                word="test",
                difficulty_level="A1",
                language="en",
                definition="a" * 2001,  # Exceeds 2000 character limit
            )

        assert "definition" in str(exc_info.value)

    def test_When_lemma_contains_invalid_characters_Then_validation_error(self):
        """Test lemma with invalid characters is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordDTO(word="test", lemma="test<script>", difficulty_level="A1", language="en")

        assert "Word contains invalid characters" in str(exc_info.value)


class TestUserProgressDTOValidation:
    """Test UserProgressDTO validation"""

    def test_When_valid_user_progress_data_Then_dto_created(self):
        """Test valid user progress data creates DTO successfully"""
        # Arrange & Act
        dto = UserProgressDTO(
            user_id=123, word="test", language="en", is_known=True, review_count=5, confidence_level=0.8
        )

        # Assert
        assert dto.user_id == 123
        assert dto.word == "test"
        assert dto.is_known is True

    def test_When_user_id_zero_Then_validation_error(self):
        """Test user_id of 0 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProgressDTO(user_id=0, word="test", language="en", is_known=True)

        assert "user_id" in str(exc_info.value)

    def test_When_user_id_negative_Then_validation_error(self):
        """Test negative user_id is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProgressDTO(user_id=-1, word="test", language="en", is_known=True)

        assert "user_id" in str(exc_info.value)

    def test_When_review_count_negative_Then_validation_error(self):
        """Test negative review_count is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProgressDTO(user_id=1, word="test", language="en", is_known=True, review_count=-1)

        assert "review_count" in str(exc_info.value)

    def test_When_confidence_level_above_one_Then_validation_error(self):
        """Test confidence_level above 1.0 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProgressDTO(user_id=1, word="test", language="en", is_known=True, confidence_level=1.5)

        assert "confidence_level" in str(exc_info.value)

    def test_When_confidence_level_below_zero_Then_validation_error(self):
        """Test confidence_level below 0.0 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProgressDTO(user_id=1, word="test", language="en", is_known=True, confidence_level=-0.1)

        assert "confidence_level" in str(exc_info.value)


class TestVocabularySearchDTOSQLInjectionPrevention:
    """Test SQL injection prevention in search queries"""

    def test_When_valid_search_query_Then_dto_created(self):
        """Test valid search query creates DTO successfully"""
        # Arrange & Act
        dto = VocabularySearchDTO(query="hello", results=[], total_matches=0)

        # Assert
        assert dto.query == "hello"

    def test_When_query_contains_semicolon_Then_removed(self):
        """Test semicolon is removed from query"""
        # Arrange & Act
        dto = VocabularySearchDTO(query="test; DROP TABLE", results=[], total_matches=0)

        # Assert
        assert ";" not in dto.query
        assert dto.query == "test DROP TABLE"

    def test_When_query_contains_single_quote_Then_removed(self):
        """Test single quotes are removed from query"""
        # Arrange & Act
        dto = VocabularySearchDTO(query="test' OR '1'='1", results=[], total_matches=0)

        # Assert
        assert "'" not in dto.query
        assert dto.query == "test OR 1=1"

    def test_When_query_contains_double_quote_Then_removed(self):
        """Test double quotes are removed from query"""
        # Arrange & Act
        dto = VocabularySearchDTO(query='test" OR "1"="1', results=[], total_matches=0)

        # Assert
        assert '"' not in dto.query

    def test_When_query_contains_backslash_Then_removed(self):
        """Test backslashes are removed from query"""
        # Arrange & Act
        dto = VocabularySearchDTO(query="test\\x00", results=[], total_matches=0)

        # Assert
        assert "\\" not in dto.query

    def test_When_query_all_special_chars_Then_validation_error(self):
        """Test query with only special characters is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularySearchDTO(query="';\"\\", results=[], total_matches=0)

        assert "Query cannot be empty after sanitization" in str(exc_info.value)

    def test_When_query_has_leading_trailing_spaces_Then_trimmed(self):
        """Test query with leading/trailing spaces is trimmed"""
        # Arrange & Act
        dto = VocabularySearchDTO(query="  test  ", results=[], total_matches=0)

        # Assert
        assert dto.query == "test"

    def test_When_query_too_short_Then_validation_error(self):
        """Test query with less than 1 character is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularySearchDTO(query="", results=[], total_matches=0)

        assert "query" in str(exc_info.value)

    def test_When_query_too_long_Then_validation_error(self):
        """Test query exceeding max length is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularySearchDTO(
                query="a" * 201,  # Exceeds 200 character limit
                results=[],
                total_matches=0,
            )

        assert "query" in str(exc_info.value)


class TestVocabularyLibraryDTOValidation:
    """Test VocabularyLibraryDTO validation"""

    def test_When_valid_library_data_Then_dto_created(self):
        """Test valid library data creates DTO successfully"""
        # Arrange & Act
        dto = VocabularyLibraryDTO(total_count=100, words=[], page=1, per_page=50, has_more=True)

        # Assert
        assert dto.total_count == 100
        assert dto.page == 1
        assert dto.per_page == 50

    def test_When_total_count_negative_Then_validation_error(self):
        """Test negative total_count is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyLibraryDTO(total_count=-1, words=[])

        assert "total_count" in str(exc_info.value)

    def test_When_page_zero_Then_validation_error(self):
        """Test page 0 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyLibraryDTO(total_count=0, words=[], page=0)

        assert "page" in str(exc_info.value)

    def test_When_page_exceeds_limit_Then_validation_error(self):
        """Test page exceeding 10000 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyLibraryDTO(total_count=0, words=[], page=10001)

        assert "page" in str(exc_info.value)

    def test_When_per_page_zero_Then_validation_error(self):
        """Test per_page 0 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyLibraryDTO(total_count=0, words=[], per_page=0)

        assert "per_page" in str(exc_info.value)

    def test_When_per_page_exceeds_limit_Then_validation_error(self):
        """Test per_page exceeding 1000 is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyLibraryDTO(total_count=0, words=[], per_page=1001)

        assert "per_page" in str(exc_info.value)


class TestVocabularyStatsDTOValidation:
    """Test VocabularyStatsDTO validation"""

    def test_When_valid_stats_data_Then_dto_created(self):
        """Test valid stats data creates DTO successfully"""
        # Arrange & Act
        dto = VocabularyStatsDTO(
            total_words=1000,
            known_words=250,
            unknown_words=750,
            level_distribution={"A1": 300, "A2": 400},
            recent_progress=[],
        )

        # Assert
        assert dto.total_words == 1000
        assert dto.known_words == 250
        assert dto.unknown_words == 750

    def test_When_negative_counts_Then_validation_error(self):
        """Test negative counts are rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyStatsDTO(total_words=-1, known_words=0, unknown_words=0)

        assert "total_words" in str(exc_info.value)

    def test_When_recent_progress_exceeds_limit_Then_validation_error(self):
        """Test recent_progress exceeding 100 items is rejected"""
        # Arrange
        too_many_progress = [
            UserProgressDTO(user_id=1, word=f"word_{i}", language="en", is_known=True) for i in range(101)
        ]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            VocabularyStatsDTO(total_words=0, known_words=0, unknown_words=0, recent_progress=too_many_progress)

        assert "recent_progress" in str(exc_info.value)
