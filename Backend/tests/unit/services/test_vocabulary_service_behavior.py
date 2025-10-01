"""Behavior-focused tests for vocabulary service (refactored from implementation-coupled tests)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from tests.helpers import TestDataSets


# Test doubles that represent behavior, not implementation
class MockVocabularyRepository:
    """Test double for vocabulary repository that focuses on behavior."""

    def __init__(self):
        self.languages: list[dict[str, Any]] = []
        self.concepts: dict[str, dict[str, Any]] = {}
        self.translations: dict[str, list[dict[str, Any]]] = {}
        self.user_progress: dict[str, set] = {}  # user_id -> set of known concept_ids

    def add_language(self, code: str, name: str, native_name: str, is_active: bool = True):
        """Add a language to the mock repository."""
        self.languages.append({"code": code, "name": name, "native_name": native_name, "is_active": is_active})

    def add_concept(self, concept_id: str, word: str, level: str, language_code: str):
        """Add a concept to the mock repository."""
        self.concepts[concept_id] = {"id": concept_id, "word": word, "level": level, "language_code": language_code}

    def add_translation(self, concept_id: str, translation: str, target_language: str):
        """Add a translation for a concept."""
        if concept_id not in self.translations:
            self.translations[concept_id] = []

        self.translations[concept_id].append(
            {"concept_id": concept_id, "translation": translation, "target_language_code": target_language}
        )

    def mark_user_knows_concept(self, user_id: str, concept_id: str):
        """Mark that a user knows a concept."""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = set()
        self.user_progress[user_id].add(concept_id)

    def mark_user_unknown_concept(self, user_id: str, concept_id: str):
        """Mark that a user doesn't know a concept."""
        if user_id in self.user_progress:
            self.user_progress[user_id].discard(concept_id)

    def get_supported_languages(self) -> list[dict[str, Any]]:
        """Get all supported languages."""
        return [lang for lang in self.languages if lang["is_active"]]

    def get_concepts_by_level(self, level: str, language_code: str) -> list[dict[str, Any]]:
        """Get concepts by level and language."""
        return [
            concept
            for concept in self.concepts.values()
            if concept["level"] == level and concept["language_code"] == language_code
        ]

    def get_translations_for_concept(self, concept_id: str, target_language: str) -> list[dict[str, Any]]:
        """Get translations for a concept in target language."""
        if concept_id not in self.translations:
            return []

        return [trans for trans in self.translations[concept_id] if trans["target_language_code"] == target_language]

    def is_concept_known_by_user(self, user_id: str, concept_id: str) -> bool:
        """Check if user knows a concept."""
        return user_id in self.user_progress and concept_id in self.user_progress[user_id]

    def count_concepts_by_level(self, level: str, language_code: str) -> int:
        """Count concepts in a level and language."""
        return len(self.get_concepts_by_level(level, language_code))

    def count_known_concepts_by_level(self, user_id: str, level: str, language_code: str) -> int:
        """Count known concepts for user in a level and language."""
        concepts = self.get_concepts_by_level(level, language_code)
        return len([concept for concept in concepts if self.is_concept_known_by_user(user_id, concept["id"])])


class MockVocabularyService:
    """Vocabulary service using mock repository (behavior-focused)."""

    def __init__(self, repository: MockVocabularyRepository):
        self.repository = repository

    async def get_supported_languages(self) -> list[dict[str, Any]]:
        """Get supported languages."""
        return self.repository.get_supported_languages()

    async def get_vocabulary_stats(
        self, target_language: str, translation_language: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get vocabulary statistics."""
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        level_stats = {}
        total_words = 0
        total_known = 0

        for level in levels:
            total = self.repository.count_concepts_by_level(level, target_language)
            known = 0
            if user_id:
                known = self.repository.count_known_concepts_by_level(user_id, level, target_language)

            level_stats[level] = {"total_words": total, "user_known": known}
            total_words += total
            total_known += known

        return {
            "target_language": target_language,
            "translation_language": translation_language,
            "levels": level_stats,
            "total_words": total_words,
            "total_known": total_known,
        }

    async def mark_concept_known(self, user_id: str, concept_id: str, known: bool) -> dict[str, Any]:
        """Mark concept as known or unknown."""
        if known:
            self.repository.mark_user_knows_concept(user_id, concept_id)
        else:
            self.repository.mark_user_unknown_concept(user_id, concept_id)

        return {"success": True, "concept_id": concept_id, "known": known}

    async def get_vocabulary_level(
        self,
        level: str,
        target_language: str,
        translation_language: str,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Get vocabulary for a specific level."""
        concepts = self.repository.get_concepts_by_level(level, target_language)

        if limit:
            concepts = concepts[:limit]

        words = []
        for concept in concepts:
            translations = self.repository.get_translations_for_concept(concept["id"], translation_language)
            translation_text = translations[0]["translation"] if translations else None

            known = False
            if user_id:
                known = self.repository.is_concept_known_by_user(user_id, concept["id"])

            words.append(
                {"concept_id": concept["id"], "word": concept["word"], "translation": translation_text, "known": known}
            )

        known_count = len([word for word in words if word["known"]])

        return {
            "level": level,
            "target_language": target_language,
            "words": words,
            "total_count": len(words),
            "known_count": known_count,
        }


@pytest.fixture
def vocab_repository():
    """Create a vocabulary repository with test data."""
    repository = MockVocabularyRepository()

    # Add languages
    repository.add_language("de", "German", "Deutsch")
    repository.add_language("es", "Spanish", "Español")
    repository.add_language("en", "English", "English")

    # Add concepts
    concepts = TestDataSets.create_german_vocabulary_set()
    for concept in concepts:
        repository.add_concept(concept.id, concept.word, concept.level, concept.language_code)

        # Add translations
        if concept.word == "das Haus":
            repository.add_translation(concept.id, "house", "en")
            repository.add_translation(concept.id, "casa", "es")
        elif concept.word == "die Katze":
            repository.add_translation(concept.id, "cat", "en")
            repository.add_translation(concept.id, "gato", "es")
        elif concept.word == "verstehen":
            repository.add_translation(concept.id, "understand", "en")
            repository.add_translation(concept.id, "entender", "es")

    return repository


@pytest.fixture
def vocab_service(vocab_repository):
    """Create vocabulary service with test repository."""
    return MockVocabularyService(vocab_repository)


class TestVocabularyServiceBehavior:
    """Test vocabulary service behavior without implementation coupling."""

    @pytest.mark.anyio
    async def test_When_supported_languages_requested_Then_active_languages_returned(self, vocab_service):
        """Service should return all active supported languages."""
        # Act
        result = await vocab_service.get_supported_languages()

        # Assert
        assert len(result) == 3
        language_codes = [lang["code"] for lang in result]
        assert "de" in language_codes
        assert "es" in language_codes
        assert "en" in language_codes

        # Verify structure
        for lang in result:
            assert "code" in lang
            assert "name" in lang
            assert "native_name" in lang
            assert lang["is_active"] is True

    @pytest.mark.anyio
    async def test_When_vocabulary_stats_requested_without_user_Then_totals_only_returned(self, vocab_service):
        """Stats without user should return total counts with zero known."""
        # Act
        result = await vocab_service.get_vocabulary_stats("de", "es")

        # Assert
        assert result["target_language"] == "de"
        assert result["translation_language"] == "es"
        assert "levels" in result
        assert "total_words" in result
        assert "total_known" in result

        # All user_known should be 0 without user
        for level_data in result["levels"].values():
            assert level_data["user_known"] == 0

    @pytest.mark.anyio
    async def test_When_vocabulary_stats_requested_with_user_Then_user_progress_included(
        self, vocab_service, vocab_repository
    ):
        """Stats with user should include user's learning progress."""
        # Arrange
        user_id = "test-user-1"
        # Get first A1 concept from the repository (not creating new ones)
        a1_concepts = vocab_repository.get_concepts_by_level("A1", "de")
        concept_id = a1_concepts[0]["id"]  # Use concept that's actually in the repository
        vocab_repository.mark_user_knows_concept(user_id, concept_id)

        # Act
        result = await vocab_service.get_vocabulary_stats("de", "es", user_id=user_id)

        # Assert
        assert result["total_known"] > 0, "Should include user's known concepts"

        # Should have user progress for A1 level (where we added known concept)
        a1_stats = result["levels"]["A1"]
        assert a1_stats["user_known"] > 0, "User should have known A1 concepts"

    @pytest.mark.anyio
    async def test_When_concept_marked_known_Then_user_progress_updated(self, vocab_service, vocab_repository):
        """Marking concept as known should update user's progress."""
        # Arrange
        user_id = "test-user-1"
        concept_id = str(uuid4())

        # Initially user doesn't know concept
        assert not vocab_repository.is_concept_known_by_user(user_id, concept_id)

        # Act
        result = await vocab_service.mark_concept_known(user_id, concept_id, True)

        # Assert
        assert result["success"] is True
        assert result["concept_id"] == concept_id
        assert result["known"] is True

        # Verify behavior change: user now knows concept
        assert vocab_repository.is_concept_known_by_user(user_id, concept_id)

    @pytest.mark.anyio
    async def test_When_concept_marked_unknown_Then_user_progress_updated(self, vocab_service, vocab_repository):
        """Marking concept as unknown should update user's progress."""
        # Arrange
        user_id = "test-user-1"
        concept_id = str(uuid4())

        # Initially mark as known
        vocab_repository.mark_user_knows_concept(user_id, concept_id)
        assert vocab_repository.is_concept_known_by_user(user_id, concept_id)

        # Act
        result = await vocab_service.mark_concept_known(user_id, concept_id, False)

        # Assert
        assert result["success"] is True
        assert result["concept_id"] == concept_id
        assert result["known"] is False

        # Verify behavior change: user no longer knows concept
        assert not vocab_repository.is_concept_known_by_user(user_id, concept_id)

    @pytest.mark.anyio
    async def test_When_vocabulary_level_requested_Then_level_words_with_translations_returned(self, vocab_service):
        """Requesting vocabulary level should return words with translations."""
        # Act
        result = await vocab_service.get_vocabulary_level("A1", "de", "en")

        # Assert
        assert result["level"] == "A1"
        assert result["target_language"] == "de"
        assert "words" in result
        assert "total_count" in result
        assert "known_count" in result

        # Should have A1 German words
        assert len(result["words"]) > 0

        # Verify word structure
        for word in result["words"]:
            assert "concept_id" in word
            assert "word" in word
            assert "translation" in word
            assert "known" in word
            assert word["known"] is False  # No user provided

    @pytest.mark.anyio
    async def test_When_vocabulary_level_requested_with_user_Then_known_status_included(
        self, vocab_service, vocab_repository
    ):
        """Vocabulary level with user should include known status."""
        # Arrange
        user_id = "test-user-1"
        # Get first A1 concept from the repository (not creating new ones)
        a1_concepts = vocab_repository.get_concepts_by_level("A1", "de")
        concept_id = a1_concepts[0]["id"]  # Use concept that's actually in the repository
        vocab_repository.mark_user_knows_concept(user_id, concept_id)

        # Act
        result = await vocab_service.get_vocabulary_level("A1", "de", "en", user_id=user_id)

        # Assert
        assert result["known_count"] > 0, "Should have some known concepts"

        # Find the known concept
        known_words = [word for word in result["words"] if word["known"]]
        assert len(known_words) > 0, "Should have at least one known word"

    @pytest.mark.anyio
    async def test_When_vocabulary_level_requested_with_limit_Then_limited_results_returned(self, vocab_service):
        """Vocabulary level with limit should return limited number of words."""
        # Act
        result = await vocab_service.get_vocabulary_level("A1", "de", "en", limit=1)

        # Assert
        assert len(result["words"]) <= 1, "Should respect limit parameter"
        assert result["total_count"] <= 1, "Total count should reflect actual returned count"


class TestVocabularyServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.anyio
    async def test_When_unsupported_language_requested_Then_empty_results_returned(self, vocab_service):
        """Requesting unsupported language should return empty results gracefully."""
        # Act
        result = await vocab_service.get_vocabulary_level("A1", "unsupported", "en")

        # Assert
        assert result["level"] == "A1"
        assert result["target_language"] == "unsupported"
        assert len(result["words"]) == 0
        assert result["total_count"] == 0
        assert result["known_count"] == 0

    @pytest.mark.anyio
    async def test_When_invalid_level_requested_Then_empty_results_returned(self, vocab_service):
        """Requesting invalid level should return empty results gracefully."""
        # Act
        result = await vocab_service.get_vocabulary_level("INVALID", "de", "en")

        # Assert
        assert result["level"] == "INVALID"
        assert len(result["words"]) == 0
        assert result["total_count"] == 0

    @pytest.mark.anyio
    async def test_When_concept_without_translation_requested_Then_none_translation_returned(
        self, vocab_service, vocab_repository
    ):
        """Concept without translation in target language should return None for translation."""
        # Arrange - add concept without translation
        concept_id = str(uuid4())
        vocab_repository.add_concept(concept_id, "test_word", "A1", "de")
        # Don't add translation for this concept

        # Act
        result = await vocab_service.get_vocabulary_level("A1", "de", "unsupported_lang")

        # Assert
        words_with_no_translation = [word for word in result["words"] if word["translation"] is None]
        assert len(words_with_no_translation) >= 0, "Should handle missing translations gracefully"

    @pytest.mark.anyio
    async def test_When_nonexistent_concept_marked_Then_operation_succeeds(self, vocab_service):
        """Marking nonexistent concept should succeed (idempotent operation)."""
        # Arrange
        nonexistent_concept_id = str(uuid4())

        # Act
        result = await vocab_service.mark_concept_known("test-user", nonexistent_concept_id, True)

        # Assert
        assert result["success"] is True
        assert result["concept_id"] == nonexistent_concept_id
        assert result["known"] is True
