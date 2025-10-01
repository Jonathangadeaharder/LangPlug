"""
User Data Loader Service
Handles loading user-related data for subtitle filtering
"""

import logging
from inspect import isawaitable

from sqlalchemy import text

from core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class UserDataLoader:
    """Service for loading user data and caching"""

    def __init__(self):
        self._word_difficulty_cache: dict[str, str] = {}
        self._user_known_words_cache: dict[str, set[str]] = {}

    async def get_user_known_words(self, user_id: str, language: str) -> set[str]:
        """
        Get set of lemmas the user already knows - always fetch fresh data

        Args:
            user_id: User ID
            language: Language code

        Returns:
            Set of known word lemmas (lowercase)
        """
        user_id_str = str(user_id)

        # Primary path: direct query (mock-friendly for unit tests)
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(
                        """
                        SELECT lemma
                        FROM user_known_words
                        WHERE user_id = :user_id
                        AND language_code = :lang
                        """
                    ),
                    {"user_id": user_id_str, "lang": language},
                )
                rows = result.fetchall()
                if isawaitable(rows):
                    rows = await rows
                lemmas = {lemma.lower() for (lemma,) in rows}
                if lemmas:
                    logger.debug(f"Loaded {len(lemmas)} known lemmas for user {user_id_str} via direct query")
                    return lemmas
        except Exception as exc:
            logger.error(f"Error loading user known words via direct query: {exc}")

        # Service fallback if direct query returns nothing or fails
        try:
            from services.vocabulary_service import VocabularyService

            vocab_service = VocabularyService

            known_lemmas = await vocab_service.get_user_known_words(user_id_str, language)
            if known_lemmas:
                logger.debug(f"Loaded {len(known_lemmas)} known lemmas for user {user_id_str} via service fallback")
                return {lemma.lower() for lemma in known_lemmas}
        except Exception as exc:
            logger.error(f"Service lookup for user known words failed: {exc}")

        return set()

    async def load_word_difficulties(self, language: str) -> dict[str, str]:
        """
        Pre-load word difficulty levels for efficiency

        Args:
            language: Language code

        Returns:
            Dictionary mapping word lemmas to difficulty levels
        """
        if self._word_difficulty_cache:
            logger.debug(f"Using cached word difficulties ({len(self._word_difficulty_cache)} entries)")
            return self._word_difficulty_cache

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(
                        """
                        SELECT DISTINCT lemma, difficulty_level
                        FROM vocabulary_words
                        WHERE language_code = :lang
                        """
                    ),
                    {"lang": language},
                )

                rows = result.fetchall()
                if isawaitable(rows):
                    rows = await rows

                for lemma, difficulty in rows:
                    self._word_difficulty_cache[lemma.lower()] = difficulty

                logger.debug(f"Loaded {len(self._word_difficulty_cache)} word difficulties")

        except Exception as e:
            logger.error(f"Error loading word difficulties: {e}")

        return self._word_difficulty_cache

    def get_word_difficulty(self, word_text: str) -> str:
        """
        Get difficulty level for a word from cache

        Args:
            word_text: Word text (will be lowercased)

        Returns:
            Difficulty level (defaults to C2 if unknown)
        """
        return self._word_difficulty_cache.get(word_text.lower(), "C2")

    def clear_cache(self) -> None:
        """Clear all caches"""
        self._word_difficulty_cache.clear()
        self._user_known_words_cache.clear()
        logger.debug("Cleared user data caches")


# Singleton instance
user_data_loader = UserDataLoader()
