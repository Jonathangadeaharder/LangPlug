"""
Word Filter Service
Handles filtering logic for words based on user knowledge and difficulty
"""

import logging
from typing import Any

from services.lemma_resolver import is_proper_name, lemmatize_word

from ..interface import FilteredWord, WordStatus

logger = logging.getLogger(__name__)


class WordFilter:
    """Service for filtering words based on learning criteria"""

    def __init__(self):
        self._level_ranks = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

    def filter_word(
        self,
        word: FilteredWord,
        user_known_words: set[str],
        user_level: str,
        language: str,
        word_info: dict[str, Any] | None = None,
    ) -> FilteredWord:
        """
        Apply all filtering logic to a single word

        Args:
            word: Word to filter
            user_known_words: Set of lemmas user knows
            user_level: User's CEFR level
            language: Language code
            word_info: Optional word information from vocabulary service

        Returns:
            FilteredWord with status and metadata updated
        """
        # Check if proper name - filter out immediately
        if is_proper_name(word.text, language):
            word.status = WordStatus.FILTERED_OTHER
            word.filter_reason = "Proper name (automatically filtered)"
            logger.debug(f"Filtered proper name: '{word.text}'")
            return word

        # Generate lemma using spaCy (always, no fallbacks)
        try:
            lemma = lemmatize_word(word.text, language)
        except Exception as e:
            logger.error(f"spaCy lemmatization failed for '{word.text}': {e}")
            word.status = WordStatus.FILTERED_INVALID
            word.filter_reason = f"Lemmatization failed: {e}"
            return word

        # Get difficulty from word info (fallback to C2 if not found)
        word_difficulty = word_info.get("difficulty_level", "C2") if word_info else "C2"

        # Store lemma and difficulty in metadata
        word.metadata["lemma"] = lemma
        word.metadata["difficulty_level"] = word_difficulty

        # Check user knowledge
        if self.is_known_by_user(lemma, user_known_words):
            word.status = WordStatus.FILTERED_KNOWN
            word.filter_reason = "User already knows this word"
            return word

        # Check difficulty level
        if self.is_at_or_below_user_level(word_difficulty, user_level):
            word.status = WordStatus.FILTERED_OTHER
            word.filter_reason = f"Word level ({word_difficulty}) at or below user level ({user_level})"
            return word

        # Word passed all filters - it's a learning target
        word.status = WordStatus.ACTIVE
        word.metadata.update({"user_level": user_level, "language": language})
        logger.debug(f"Word '{word.text}' -> lemma '{lemma}' (level: {word_difficulty})")
        return word

    def _extract_word_data(self, word_text: str, word_info: dict[str, Any] | None) -> tuple[str, str]:
        """
        Extract lemma and difficulty from word info

        Args:
            word_text: Original word text
            word_info: Word information dictionary

        Returns:
            Tuple of (lemma, difficulty_level)
        """
        if word_info is None:
            return word_text, "C2"

        lemma = word_info.get("lemma", word_text) or word_text
        difficulty = word_info.get("difficulty_level", "C2") or "C2"

        return lemma, difficulty

    def is_known_by_user(self, lemma: str, user_known_words: set[str]) -> bool:
        """
        Check if user knows the word lemma

        Args:
            lemma: Word lemma
            user_known_words: Set of known lemmas

        Returns:
            True if user knows the word
        """
        return lemma.lower() in user_known_words

    def is_at_or_below_user_level(self, word_difficulty: str, user_level: str) -> bool:
        """
        Check if word difficulty is at or below user's level

        Args:
            word_difficulty: Word difficulty level (A1-C2)
            user_level: User's level (A1-C2)

        Returns:
            True if word is at or below user level
        """
        user_level_rank = self._get_level_rank(user_level)
        word_level_rank = self._get_level_rank(word_difficulty)

        return word_level_rank <= user_level_rank

    def _get_level_rank(self, level: str) -> int:
        """
        Convert CEFR level to numeric rank for comparison

        Args:
            level: CEFR level (A1-C2)

        Returns:
            Numeric rank (1-6)
        """
        return self._level_ranks.get(level.upper(), 3)  # Default to B1 level

    def create_filtered_word(
        self,
        text: str,
        start_time: float,
        end_time: float,
        status: WordStatus = WordStatus.ACTIVE,
        filter_reason: str | None = None,
        metadata: dict | None = None,
    ) -> FilteredWord:
        """
        Create a FilteredWord with specified properties

        Args:
            text: Word text
            start_time: Start time in seconds
            end_time: End time in seconds
            status: Word status
            filter_reason: Reason for filtering (if filtered)
            metadata: Additional metadata

        Returns:
            FilteredWord instance
        """
        return FilteredWord(
            text=text,
            start_time=start_time,
            end_time=end_time,
            status=status,
            filter_reason=filter_reason,
            confidence=None,
            metadata=metadata or {},
        )


# Singleton instance
word_filter = WordFilter()
