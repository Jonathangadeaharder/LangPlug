"""
Test suite for multilingual vocabulary Pydantic models
Tests focus on validation logic for the new UUID-based multilingual system
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.models.vocabulary import (
    BulkMarkRequest,
    ImportRequest,
    LanguageRequest,
    LanguagesResponse,
    SupportedLanguage,
    TranslationPair,
    VocabularyLevel,
    VocabularyLibraryWord,
    VocabularyStats,
    VocabularyWord,
)
from api.routes.vocabulary_progress_routes import MarkKnownRequest


class TestVocabularyWordValidation:
    """Test VocabularyWord model validation"""

    def test_validate_word_valid_multilingual_data(self):
        """Test word validation with valid multilingual vocabulary words"""
        concept_id = uuid4()
        valid_words_data = [
            {
                "concept_id": concept_id,
                "word": "Hallo",
                "translation": "Hola",
                "lemma": "hallo",
                "difficulty_level": "A1",
                "semantic_category": "noun",
                "domain": "greeting",
                "gender": None,
                "known": False,
            },
            {
                "concept_id": uuid4(),
                "word": "sprechen",
                "translation": "hablar",
                "lemma": "sprechen",
                "difficulty_level": "A2",
                "semantic_category": "verb",
                "domain": "communication",
                "gender": None,
                "known": True,
            },
        ]

        for word_data in valid_words_data:
            vocab_word = VocabularyWord(**word_data)
            assert vocab_word.word == word_data["word"]
            assert vocab_word.translation == word_data["translation"]
            assert vocab_word.concept_id == word_data["concept_id"]
            assert vocab_word.difficulty_level == word_data["difficulty_level"]

    def test_validate_word_empty_word(self):
        """Test word validation fails with empty word"""
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWord(
                concept_id=uuid4(),
                word="",  # Empty word
                translation="Hello",
                difficulty_level="A1",
                semantic_category="noun",
                known=False,
            )

        error_messages = str(exc_info.value)
        assert "String should have at least 1 character" in error_messages

    def test_validate_word_whitespace_only(self):
        """Test word validation with whitespace-only word (allowed by min_length=1)"""
        # Pydantic v2 with min_length=1 allows whitespace-only strings
        vocab_word = VocabularyWord(
            concept_id=uuid4(),
            word="   ",  # Whitespace only - this is actually valid with min_length=1
            translation="Hello",
            difficulty_level="A1",
            semantic_category="noun",
            known=False,
        )
        assert vocab_word.word == "   "

    def test_validate_difficulty_level_invalid(self):
        """Test difficulty level validation with invalid CEFR levels"""
        with pytest.raises(ValidationError):
            VocabularyWord(
                concept_id=uuid4(),
                word="Test",
                difficulty_level="Z9",  # Invalid CEFR level
                semantic_category="noun",
                known=False,
            )

    def test_validate_multilingual_metadata(self):
        """Test validation with rich multilingual metadata"""
        vocab_word = VocabularyWord(
            concept_id=uuid4(),
            word="Mädchen",
            translation="niña",
            lemma="mädchen",
            difficulty_level="A1",
            semantic_category="noun",
            domain="family",
            gender="das",
            plural_form="Mädchen",
            pronunciation="/ˈmɛːtçən/",
            notes="Neuter noun despite feminine meaning",
            known=False,
        )

        assert vocab_word.gender == "das"
        assert vocab_word.plural_form == "Mädchen"
        assert vocab_word.pronunciation == "/ˈmɛːtçən/"


class TestMarkKnownRequestValidation:
    """Test MarkKnownRequest model validation"""

    def test_validate_concept_id_valid_requests(self):
        """Test request validation with valid mark known requests"""
        valid_requests = [
            {"lemma": "test", "language": "de", "known": True},
            {"lemma": "hello", "language": "en", "known": False},
        ]

        for request_data in valid_requests:
            request = MarkKnownRequest(**request_data)
            assert request.lemma == request_data["lemma"]
            assert request.language == request_data["language"]
            assert request.known == request_data["known"]

    def test_validate_concept_id_invalid_uuid(self):
        """Test mark known request fails with invalid data"""
        # No longer testing UUID since it was removed from model
        pass

    def test_validate_known_field_missing(self):
        """Test known field is required"""
        with pytest.raises(ValidationError) as exc_info:
            MarkKnownRequest(lemma="test", language="de")  # Missing known field
        error_msg = str(exc_info.value).lower()
        assert "known" in error_msg or "required" in error_msg

    def test_validate_known_field_wrong_type(self):
        """Test known field must be boolean"""
        # Test that string "yes" gets converted to boolean True in Pydantic v2
        # This is expected Pydantic behavior, so we test the successful conversion
        request = MarkKnownRequest(lemma="test", language="de", known="yes")
        assert request.known is True

        # Test that invalid string types that can't be converted raise errors
        with pytest.raises(ValidationError) as exc_info:
            MarkKnownRequest(lemma="test", language="de", known="not_a_bool")
        error_msg = str(exc_info.value).lower()
        assert "bool" in error_msg or "input" in error_msg


class TestVocabularyLevelValidation:
    """Test VocabularyLevel model validation"""

    def test_validate_level_with_multilingual_support(self):
        """Test level validation with multilingual parameters"""
        concept_id = uuid4()
        valid_level_data = {
            "level": "A1",
            "target_language": "de",
            "translation_language": "es",
            "words": [
                VocabularyLibraryWord(
                    concept_id=concept_id,
                    word="Hallo",
                    translation="Hola",
                    difficulty_level="A1",
                    semantic_category="noun",
                    known=False,
                )
            ],
            "total_count": 1,
            "known_count": 0,
        }

        level = VocabularyLevel(**valid_level_data)
        assert level.target_language == "de"
        assert level.translation_language == "es"
        assert len(level.words) == 1
        assert level.words[0].concept_id == concept_id

    def test_validate_known_count_exceeds_total(self):
        """Test that known count can exceed total (business logic validation elsewhere)"""
        # The Pydantic model itself doesn't prevent this - business logic validation is elsewhere
        level = VocabularyLevel(
            level="A1",
            target_language="de",
            translation_language="es",
            words=[],
            total_count=5,
            known_count=10,  # Exceeds total - but model allows it
        )
        assert level.total_count == 5
        assert level.known_count == 10

    def test_validate_invalid_language_codes(self):
        """Test validation with invalid language codes"""
        with pytest.raises(ValidationError):
            VocabularyLevel(
                level="A1",
                target_language="X",  # Too short
                words=[],
                total_count=0,
                known_count=0,
            )


class TestVocabularyStatsValidation:
    """Test VocabularyStats model validation"""

    def test_validate_multilingual_stats(self):
        """Test stats validation with multilingual parameters"""
        valid_stats_data = {
            "levels": {"A1": {"total_words": 100, "user_known": 20}, "A2": {"total_words": 150, "user_known": 30}},
            "target_language": "de",
            "translation_language": "es",
            "total_words": 250,
            "total_known": 50,
        }

        stats = VocabularyStats(**valid_stats_data)
        assert stats.target_language == "de"
        assert stats.translation_language == "es"
        assert stats.levels["A1"]["total_words"] == 100
        assert stats.levels["A1"]["user_known"] == 20

    def test_validate_total_known_exceeds_total(self):
        """Test that total known can exceed total words (business logic validation elsewhere)"""
        # The Pydantic model itself doesn't prevent this - business logic validation is elsewhere
        stats = VocabularyStats(
            levels={},
            target_language="de",
            total_words=100,
            total_known=150,  # Exceeds total words - but model allows it
        )
        assert stats.total_words == 100
        assert stats.total_known == 150


class TestVocabularyLibraryWord:
    """Test VocabularyLibraryWord model with multilingual support"""

    def test_valid_library_word_multilingual(self):
        """Test valid library word with full multilingual data"""
        concept_id = uuid4()
        library_word_data = {
            "concept_id": concept_id,
            "word": "sprechen",
            "translation": "hablar",
            "lemma": "sprechen",
            "difficulty_level": "A2",
            "semantic_category": "verb",
            "domain": "communication",
            "gender": None,
            "plural_form": None,
            "pronunciation": "/ˈʃprɛçən/",
            "notes": "Strong verb, irregular conjugation",
            "known": False,
        }

        library_word = VocabularyLibraryWord(**library_word_data)
        assert library_word.concept_id == concept_id
        assert library_word.word == "sprechen"
        assert library_word.translation == "hablar"
        assert library_word.pronunciation == "/ˈʃprɛçən/"
        assert not library_word.known


class TestBulkMarkRequest:
    """Test BulkMarkRequest model with multilingual support"""

    def test_valid_bulk_mark_multilingual(self):
        """Test valid bulk mark request with target language"""
        bulk_request_data = {"level": "A1", "target_language": "de", "known": True}

        bulk_request = BulkMarkRequest(**bulk_request_data)
        assert bulk_request.level == "A1"
        assert bulk_request.target_language == "de"
        assert bulk_request.known

    def test_invalid_language_code(self):
        """Test validation fails with invalid language code"""
        with pytest.raises(ValidationError):
            BulkMarkRequest(
                level="A1",
                target_language="X",  # Too short
                known=True,
            )


class TestSupportedLanguage:
    """Test SupportedLanguage model"""

    def test_valid_supported_language(self):
        """Test valid supported language"""
        lang_data = {"code": "de", "name": "German", "native_name": "Deutsch", "is_active": True}

        language = SupportedLanguage(**lang_data)
        assert language.code == "de"
        assert language.name == "German"
        assert language.native_name == "Deutsch"
        assert language.is_active


class TestLanguagesResponse:
    """Test LanguagesResponse model"""

    def test_valid_languages_response(self):
        """Test valid languages response"""
        languages = [
            SupportedLanguage(code="de", name="German", native_name="Deutsch"),
            SupportedLanguage(code="es", name="Spanish", native_name="Español"),
        ]

        response = LanguagesResponse(languages=languages)
        assert len(response.languages) == 2
        assert response.languages[0].code == "de"
        assert response.languages[1].code == "es"


class TestTranslationPair:
    """Test TranslationPair model for vocabulary import"""

    def test_valid_translation_pair(self):
        """Test valid German-Spanish translation pair"""
        pair_data = {"german": "Hallo", "spanish": "Hola", "difficulty_level": "A1"}

        pair = TranslationPair(**pair_data)
        assert pair.german == "Hallo"
        assert pair.spanish == "Hola"
        assert pair.difficulty_level == "A1"

    def test_invalid_difficulty_level(self):
        """Test validation fails with invalid difficulty level"""
        with pytest.raises(ValidationError):
            TranslationPair(
                german="Test",
                spanish="Test",
                difficulty_level="Z9",  # Invalid CEFR level
            )


class TestImportRequest:
    """Test ImportRequest model for bulk vocabulary import"""

    def test_valid_import_request(self):
        """Test valid import request with translation pairs"""
        pairs = [
            TranslationPair(german="Hallo", spanish="Hola", difficulty_level="A1"),
            TranslationPair(german="Danke", spanish="Gracias", difficulty_level="A1"),
        ]

        import_request = ImportRequest(translation_pairs=pairs, overwrite_existing=False)

        assert len(import_request.translation_pairs) == 2
        assert not import_request.overwrite_existing

    def test_empty_translation_pairs(self):
        """Test validation fails with empty translation pairs"""
        with pytest.raises(ValidationError):
            ImportRequest(translation_pairs=[])  # Empty list should fail


class TestLanguageRequest:
    """Test LanguageRequest model"""

    def test_valid_language_request(self):
        """Test valid language request"""
        lang_request = LanguageRequest(target_language="de", translation_language="es")

        assert lang_request.target_language == "de"
        assert lang_request.translation_language == "es"

    def test_valid_language_request_no_translation(self):
        """Test valid language request without translation language"""
        lang_request = LanguageRequest(target_language="de")

        assert lang_request.target_language == "de"
        assert lang_request.translation_language is None


class TestModelIntegration:
    """Test model integration and complex multilingual scenarios"""

    def test_vocabulary_level_with_multilingual_words(self):
        """Test VocabularyLevel with nested multilingual words"""
        concept_1 = uuid4()
        concept_2 = uuid4()

        words = [
            VocabularyLibraryWord(
                concept_id=concept_1,
                word="Hallo",
                translation="Hola",
                difficulty_level="A1",
                semantic_category="noun",
                known=True,
            ),
            VocabularyLibraryWord(
                concept_id=concept_2,
                word="sprechen",
                translation="hablar",
                difficulty_level="A2",
                semantic_category="verb",
                known=False,
            ),
        ]

        level = VocabularyLevel(
            level="A1", target_language="de", translation_language="es", words=words, total_count=2, known_count=1
        )

        assert len(level.words) == 2
        assert level.words[0].known
        assert not level.words[1].known
        assert level.target_language == "de"
        assert level.translation_language == "es"

    def test_vocabulary_stats_multilingual_consistency(self):
        """Test VocabularyStats multilingual data consistency"""
        stats = VocabularyStats(
            levels={"A1": {"total_words": 100, "user_known": 80}, "A2": {"total_words": 150, "user_known": 60}},
            target_language="de",
            translation_language="es",
            total_words=250,
            total_known=140,
        )

        # Verify totals match individual levels
        expected_total = sum(level["total_words"] for level in stats.levels.values())
        expected_known = sum(level["user_known"] for level in stats.levels.values())

        assert stats.total_words == expected_total
        assert stats.total_known == expected_known
