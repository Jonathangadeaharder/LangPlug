"""
Learning Level Service
Handles user learning level determination based on vocabulary size
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .word_status_service import word_status_service


class LearningLevelService:
    """Service for managing user learning levels"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.word_status = word_status_service

    async def get_learning_level(self, session: AsyncSession, user_id: str, language: str = "en") -> str:
        """
        Get user's current learning level based on vocabulary size

        Args:
            session: Database session
            user_id: User ID
            language: Language code

        Returns:
            Learning level (A1, A2, B1, B2, C1, C2)
        """
        try:
            # Determine level based on vocabulary size
            known_words = await self.word_status.get_known_words(session, user_id, language)
            known_words_count = len(known_words)

            if known_words_count < 500:
                return "A1"
            elif known_words_count < 1500:
                return "A2"
            elif known_words_count < 3000:
                return "B1"
            elif known_words_count < 5000:
                return "B2"
            elif known_words_count < 8000:
                return "C1"
            else:
                return "C2"

        except Exception as e:
            self.logger.error(f"Error getting learning level: {e}")
            return "A2"  # Default level

    async def set_learning_level(self, user_id: str, level: str) -> bool:
        """
        Set user's learning level (currently computed dynamically)

        Args:
            user_id: User ID
            level: Learning level to set

        Returns:
            True if successful

        Note:
            In this implementation, level is computed based on vocabulary size.
            Could be extended to store explicit user level preferences.
        """
        self.logger.info(f"Learning level for {user_id} would be set to {level} (computed dynamically)")
        return True


# Singleton instance
learning_level_service = LearningLevelService()
