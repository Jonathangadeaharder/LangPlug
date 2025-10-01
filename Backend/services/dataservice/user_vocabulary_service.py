"""
User Vocabulary Data Service Implementation
Facade delegating to focused services for user vocabulary management
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from core.database import get_async_session
from services.user_vocabulary import (
    learning_level_service,
    learning_progress_service,
    learning_stats_service,
    vocabulary_repository,
    word_status_service,
)


class SQLiteUserVocabularyService:
    """
    SQLite-based implementation of user vocabulary service
    Facade pattern delegating to focused sub-services
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.repository = vocabulary_repository
        self.word_status = word_status_service
        self.learning_progress = learning_progress_service
        self.learning_level = learning_level_service
        self.learning_stats = learning_stats_service

    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        async for session in get_async_session():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def is_word_known(self, user_id: str, word: str, language: str = "en") -> bool:
        """Check if user knows a specific word"""
        try:
            async with self.get_session() as session:
                return await self.word_status.is_word_known(session, user_id, word, language)
        except Exception as e:
            self.logger.error(f"Error checking if word is known: {e}")
            return False

    async def get_known_words(self, user_id: str, language: str = "en") -> list[str]:
        """Get all words known by user"""
        try:
            async with self.get_session() as session:
                return await self.word_status.get_known_words(session, user_id, language)
        except Exception as e:
            self.logger.error(f"Error getting known words: {e}")
            return []

    async def mark_word_learned(self, user_id: str, word: str, language: str = "en") -> bool:
        """Mark word as learned by user"""
        try:
            async with self.get_session() as session:
                return await self.learning_progress.mark_word_learned(session, user_id, word, language)
        except Exception as e:
            self.logger.error(f"Error marking word as learned: {e}")
            return False

    async def get_learning_level(self, user_id: str, language: str = "en") -> str:
        """Get user's current learning level"""
        try:
            async with self.get_session() as session:
                return await self.learning_level.get_learning_level(session, user_id, language)
        except Exception as e:
            self.logger.error(f"Error getting learning level: {e}")
            return "A2"  # Default level

    async def set_learning_level(self, user_id: str, level: str) -> bool:
        """Set user's learning level (stored implicitly based on vocabulary)"""
        return await self.learning_level.set_learning_level(user_id, level)

    async def add_known_words(self, user_id: str, words: list[str], language: str = "en") -> bool:
        """Add multiple words to user's known vocabulary using batch operations"""
        try:
            async with self.get_session() as session:
                return await self.learning_progress.add_known_words(session, user_id, words, language)
        except Exception as e:
            self.logger.error(f"Error adding known words in batch: {e}")
            return False

    async def get_learning_statistics(self, user_id: str, language: str = "en") -> dict[str, Any]:
        """Get learning statistics for user"""
        try:
            async with self.get_session() as session:
                return await self.learning_stats.get_learning_statistics(session, user_id, language)
        except Exception as e:
            self.logger.error(f"Error getting learning statistics: {e}")
            return {"total_known": 0, "total_learned": 0, "error": str(e)}

    async def get_word_learning_history(self, user_id: str, word: str, language: str = "en") -> list[dict[str, Any]]:
        """Get learning history for a specific word"""
        try:
            async with self.get_session() as session:
                return await self.learning_stats.get_word_learning_history(session, user_id, word, language)
        except Exception as e:
            self.logger.error(f"Error getting word learning history: {e}")
            return []

    async def get_words_by_confidence(
        self, user_id: str, confidence_level: int, language: str = "en", limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get words by confidence level"""
        try:
            async with self.get_session() as session:
                return await self.learning_stats.get_words_by_confidence(
                    session, user_id, confidence_level, language, limit
                )
        except Exception as e:
            self.logger.error(f"Error getting words by confidence: {e}")
            return []

    async def remove_word(self, user_id: str, word: str, language: str = "en") -> bool:
        """Remove a word from user's learning progress"""
        try:
            async with self.get_session() as session:
                return await self.learning_progress.remove_word(session, user_id, word, language)
        except Exception as e:
            self.logger.error(f"Error removing word: {e}")
            return False


# Singleton instance
user_vocabulary_service = SQLiteUserVocabularyService()
