"""
Word Status Service
Handles querying word status (known/unknown) for users
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class WordStatusService:
    """Service for querying word status"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def is_word_known(self, session: AsyncSession, user_id: str, word: str, language: str = "en") -> bool:
        """
        Check if user knows a specific word

        Args:
            session: Database session
            user_id: User ID
            word: Word to check
            language: Language code

        Returns:
            True if user knows the word, False otherwise
        """
        try:
            query = text("""
                SELECT COUNT(*) as count
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = :user_id AND v.word = :word AND v.language = :language
            """)
            result = await session.execute(query, {"user_id": user_id, "word": word.lower(), "language": language})
            row = result.fetchone()
            return row[0] > 0 if row else False

        except Exception as e:
            self.logger.error(f"Error checking if word is known: {e}")
            return False

    async def get_known_words(self, session: AsyncSession, user_id: str, language: str = "en") -> list[str]:
        """
        Get all words known by user

        Args:
            session: Database session
            user_id: User ID
            language: Language code

        Returns:
            List of known words
        """
        try:
            query = text("""
                SELECT v.word
                FROM vocabulary v
                JOIN user_learning_progress ulp ON v.id = ulp.word_id
                WHERE ulp.user_id = :user_id AND v.language = :language
                ORDER BY v.word
            """)
            result = await session.execute(query, {"user_id": user_id, "language": language})
            return [row[0] for row in result.fetchall()]

        except Exception as e:
            self.logger.error(f"Error getting known words: {e}")
            return []

    async def get_words_by_confidence(
        self, session: AsyncSession, user_id: str, confidence_level: int, language: str = "en", limit: int = 100
    ) -> list[dict]:
        """
        Get words by confidence level

        Args:
            session: Database session
            user_id: User ID
            confidence_level: Confidence level to filter by
            language: Language code
            limit: Maximum number of words to return

        Returns:
            List of word dictionaries with confidence info
        """
        try:
            query = text("""
                SELECT v.word, ulp.confidence_level, ulp.last_reviewed_at
                FROM vocabulary v
                JOIN user_learning_progress ulp ON v.id = ulp.word_id
                WHERE ulp.user_id = :user_id
                AND v.language = :language
                AND ulp.confidence_level = :confidence_level
                ORDER BY ulp.last_reviewed_at DESC
                LIMIT :limit
            """)
            result = await session.execute(
                query, {"user_id": user_id, "language": language, "confidence_level": confidence_level, "limit": limit}
            )

            return [
                {"word": row[0], "confidence_level": row[1], "last_reviewed_at": row[2]} for row in result.fetchall()
            ]

        except Exception as e:
            self.logger.error(f"Error getting words by confidence: {e}")
            return []


# Singleton instance
word_status_service = WordStatusService()
