"""
Vocabulary building service for filtering operations
"""

import logging
import uuid
from inspect import isawaitable
from typing import Any

from services.filterservice.interface import FilteredWord
from services.nlp.lemma_resolver import lemmatize_word

logger = logging.getLogger(__name__)


class VocabularyBuilderService:
    """Builds vocabulary words from blocker words with database lookup and caching"""

    def __init__(self):
        self.concept_cache: dict[str, dict[str, Any | None]] = {}
        self.lemma_cache: dict[str, str | None] = {}

    async def build_vocabulary_words(
        self, blocker_words: list[FilteredWord], target_language: str, return_dict: bool = True
    ) -> list[Any]:
        """
        Convert blocker words to VocabularyWord objects with real concept IDs

        Args:
            blocker_words: List of filtered words that block comprehension
            target_language: Target language code
            return_dict: Whether to return dicts or VocabularyWord objects

        Returns:
            List of VocabularyWord objects or dicts
        """
        from core.database import AsyncSessionLocal

        vocabulary_words: list[Any] = []

        async with AsyncSessionLocal() as session:
            for blocker in blocker_words:
                word_text = blocker.text.lower()

                # Check cache first
                cache_entry = self.concept_cache.get(word_text)
                if cache_entry is not None:
                    concept_id = cache_entry["concept_id"]
                    cached_level = cache_entry["level"]
                    cached_word = cache_entry["db_word"]
                    cached_lemma = cache_entry["db_lemma"]
                    resolved_lemma = cache_entry.get("resolved_lemma")
                else:
                    # Get or compute lemma
                    resolved_lemma = self._get_or_compute_lemma(word_text, blocker.text, target_language)

                    # Generate candidate forms for lookup
                    candidate_values = self.generate_candidate_forms(word_text, resolved_lemma, target_language)

                    # Look up concept in database
                    row = await self._lookup_concept_from_db(candidate_values, target_language, session)

                    # Process lookup result
                    if row:
                        concept_uuid = uuid.UUID(str(row[0]))
                        logger.info(
                            "Mapped blocker word '%s' (lemma '%s') -> concept %s (word='%s', lemma='%s', level=%s)",
                            blocker.text,
                            resolved_lemma or word_text,
                            concept_uuid,
                            row[2],
                            row[3],
                            row[1],
                        )
                        concept_id, cached_level, cached_word, cached_lemma = (concept_uuid, row[1], row[2], row[3])
                    else:
                        logger.warning(
                            "Concept not found for word '%s' (lemma '%s') in language '%s'",
                            blocker.text,
                            resolved_lemma or word_text,
                            target_language,
                        )
                        concept_id, cached_level, cached_word, cached_lemma = (None, None, None, None)

                    # Cache the result
                    self.concept_cache[word_text] = self._create_cache_entry(
                        concept_id, cached_level, cached_word, cached_lemma, resolved_lemma
                    )

                # Create vocabulary word
                final_lemma = cached_lemma or resolved_lemma or word_text
                vocab_word = self._create_vocabulary_word(
                    blocker.text, final_lemma, target_language, cached_level, blocker.metadata, concept_id, return_dict
                )
                vocabulary_words.append(vocab_word)

        return vocabulary_words

    def _get_or_compute_lemma(self, word_text: str, blocker_text: str, target_language: str) -> str | None:
        """Get lemma from cache or compute it"""
        resolved_lemma = self.lemma_cache.get(word_text)
        if word_text not in self.lemma_cache:
            resolved_lemma = lemmatize_word(blocker_text, target_language)
            self.lemma_cache[word_text] = resolved_lemma
        return resolved_lemma

    async def _lookup_concept_from_db(
        self, candidate_values: tuple[str, ...], target_language: str, session
    ) -> tuple | None:
        """Look up concept from database by candidate forms"""
        from sqlalchemy import func, or_, select

        from database.models import VocabularyWord

        stmt = (
            select(
                VocabularyWord.id,
                VocabularyWord.difficulty_level,
                VocabularyWord.word,
                VocabularyWord.lemma,
            )
            .where(
                VocabularyWord.language == target_language,
                or_(
                    func.lower(VocabularyWord.word).in_(candidate_values),
                    func.lower(VocabularyWord.lemma).in_(candidate_values),
                ),
            )
            .limit(1)
        )

        result = await session.execute(stmt)
        row = result.first()
        if isawaitable(row):
            row = await row
        return row

    def _create_cache_entry(
        self,
        concept_id: Any | None,
        level: str | None,
        db_word: str | None,
        db_lemma: str | None,
        resolved_lemma: str | None,
    ) -> dict[str, Any | None]:
        """Create cache entry for concept lookup"""
        return {
            "concept_id": concept_id,
            "level": level,
            "db_word": db_word,
            "db_lemma": db_lemma,
            "resolved_lemma": resolved_lemma,
        }

    def _create_vocabulary_word(
        self,
        blocker_text: str,
        final_lemma: str,
        target_language: str,
        cached_level: str | None,
        blocker_metadata: dict,
        concept_id: Any | None,
        return_dict: bool,
    ) -> Any:
        """Create VocabularyWord object from blocker and concept info"""
        from database.models import VocabularyWord

        vocab_word = VocabularyWord(
            word=blocker_text,
            lemma=final_lemma,
            language=target_language,
            difficulty_level=(cached_level or blocker_metadata.get("difficulty_level") or "C2"),
            translation_en="",
        )

        if concept_id:
            vocab_word.id = concept_id

        return vocab_word.dict() if return_dict else vocab_word

    def generate_candidate_forms(
        self,
        word_text: str,
        resolved_lemma: str | None,
        language: str,
    ) -> tuple[str, ...]:
        """Generate candidate word forms for database lookup"""
        word_text = (word_text or "").strip().lower()
        forms: set[str] = {word_text}

        if resolved_lemma:
            forms.add(resolved_lemma.strip().lower())

        if language.lower() == "de":
            forms.update(self._german_heuristic_forms(word_text))

        return tuple(sorted({form for form in forms if form}))

    @staticmethod
    def _german_heuristic_forms(word_text: str) -> set[str]:
        """Generate German language-specific word forms"""
        forms: set[str] = set()

        # Common adjective/adverb endings
        adjective_suffixes = (
            "erer",
            "eren",
            "erem",
            "ere",
            "er",
            "em",
            "en",
            "es",
            "e",
            "st",
            "ste",
            "sten",
            "ster",
            "stes",
            "stem",
        )

        for suffix in adjective_suffixes:
            if word_text.endswith(suffix) and len(word_text) - len(suffix) >= 3:
                forms.add(word_text[: -len(suffix)])

        # Common noun suffixes
        noun_suffixes = ("ern", "er", "en", "e", "n", "s")
        for suffix in noun_suffixes:
            if word_text.endswith(suffix) and len(word_text) - len(suffix) >= 3:
                forms.add(word_text[: -len(suffix)])

        return forms


# Global instance
vocabulary_builder_service = VocabularyBuilderService()


def get_vocabulary_builder_service() -> VocabularyBuilderService:
    """Get the global vocabulary builder service instance"""
    return vocabulary_builder_service
