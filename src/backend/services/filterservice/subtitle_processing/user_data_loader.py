"""
User Data Loader Service
Handles loading user-related data for subtitle filtering
"""

from inspect import isawaitable

from sqlalchemy import text

from core.config.logging_config import get_logger
from core.database import AsyncSessionLocal

logger = get_logger(__name__)


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

        # Primary path: direct query from user_vocabulary_progress table
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(
                        """
                        SELECT DISTINCT lemma
                        FROM user_vocabulary_progress
                        WHERE user_id = :user_id
                        AND language = :lang
                        AND is_known = 1
                        """
                    ),
                    {"user_id": user_id_str, "lang": language},
                )
                rows = result.fetchall()
                if isawaitable(rows):
                    rows = await rows
                lemmas = {lemma.lower() for (lemma,) in rows}
                logger.debug("Loaded known lemmas", count=len(lemmas), user_id=user_id_str)
                return lemmas
        except Exception as exc:
            logger.error("Error loading user known words", error=str(exc))
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
            logger.debug("Using cached word difficulties", count=len(self._word_difficulty_cache))
            return self._word_difficulty_cache

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(
                        """
                        SELECT DISTINCT lemma, difficulty_level
                        FROM vocabulary_words
                        WHERE language = :lang
                        """
                    ),
                    {"lang": language},
                )

                rows = result.fetchall()
                if isawaitable(rows):
                    rows = await rows

                for lemma, difficulty in rows:
                    self._word_difficulty_cache[lemma.lower()] = difficulty

                logger.debug("Loaded word difficulties", count=len(self._word_difficulty_cache))

        except Exception as e:
            logger.error("Error loading word difficulties", error=str(e))

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
