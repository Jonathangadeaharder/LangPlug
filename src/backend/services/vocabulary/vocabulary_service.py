"""
Vocabulary Service Facade

Modern facade pattern implementation for vocabulary operations, delegating to specialized sub-services.
This module provides a unified interface for vocabulary querying, progress tracking, and statistics.

Key Components:
    - VocabularyService: Main facade coordinating sub-services
    - vocabulary_query_service: Word lookup and search operations
    - vocabulary_progress_service: User progress tracking and bulk operations
    - vocabulary_stats_service: Statistics and analytics

Architecture:
    This facade delegates to three specialized services:
    1. Query Service: Read operations (word info, library, search)
    2. Progress Service: Write operations (mark known, bulk updates)
    3. Stats Service: Analytics (statistics, summaries, supported languages)

Usage Example:
    ```python
    from services.vocabulary.vocabulary_service import vocabulary_service

    # Get word information
    word_info = await vocabulary_service.get_word_info("Haus", "de", db)

    # Mark word as known
    result = await vocabulary_service.mark_word_known(
        user_id=123,
        word="Haus",
        language="de",
        is_known=True,
        db=db
    )

    # Get user statistics
    stats = await vocabulary_service.get_user_vocabulary_stats(123, "de", db)
    ```

Dependencies:
    - sqlalchemy: Database operations
    - vocabulary_query_service: Word lookups
    - vocabulary_progress_service: Progress tracking
    - vocabulary_stats_service: Statistics generation

Thread Safety:
    Yes. Service instance is stateless, delegates to sub-services which handle their own concurrency.

Performance Notes:
    - Query operations: O(1) with database indexes
    - Progress updates: Transactional, may involve locking
    - Statistics: May involve aggregations, consider caching

Architecture Note:
    This facade pattern provides a clean API while delegating to specialized services.
    Maintains separation of concerns while offering convenience methods.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class VocabularyService:
    """
    Facade for vocabulary operations coordinating specialized sub-services.

    Provides a unified API for all vocabulary-related operations while delegating
    to focused services for query, progress tracking, and statistics.

    Attributes:
        query_service: Handles word lookups and searches
        progress_service: Manages user progress and bulk operations
        stats_service: Generates statistics and analytics

    Example:
        ```python
        service = VocabularyService()

        # Query operations
        word = await service.get_word_info("Haus", "de", db)
        library = await service.get_vocabulary_library(db, "de", level="A1")

        # Progress operations
        await service.mark_word_known(123, "Haus", "de", True, db)
        await service.bulk_mark_level(db, 123, "de", "A1", True)

        # Statistics
        stats = await service.get_user_vocabulary_stats(123, "de", db)
        ```

    Note:
        This is a stateless facade - all state is managed by sub-services.
        Safe to use as singleton (vocabulary_service instance).
    """

    def __init__(self):
        # Get fresh instances via factory functions to avoid global state
        from .vocabulary_progress_service import get_vocabulary_progress_service
        from .vocabulary_query_service import get_vocabulary_query_service
        from .vocabulary_stats_service import get_vocabulary_stats_service

        self.query_service = get_vocabulary_query_service()
        self.progress_service = get_vocabulary_progress_service()
        self.stats_service = get_vocabulary_stats_service()

    def _get_session(self):
        """Get database session context manager"""
        return AsyncSessionLocal()

    # ========== Query Service Methods ==========

    async def get_word_info(self, word: str, language: str, db: AsyncSession) -> dict[str, Any] | None:
        """Get vocabulary information for a word"""
        return await self.query_service.get_word_info(word, language, db)

    async def get_vocabulary_library(
        self,
        db: AsyncSession,
        language: str,
        level: str | None = None,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get vocabulary library with optional filtering"""
        return await self.query_service.get_vocabulary_library(db, language, level, user_id, limit, offset)

    async def search_vocabulary(
        self, db: AsyncSession, search_term: str, language: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search vocabulary by word or lemma"""
        return await self.query_service.search_vocabulary(db, search_term, language, limit)

    # ========== Progress Service Methods ==========

    async def mark_word_known(
        self, user_id: int, word: str, language: str, is_known: bool, db: AsyncSession
    ) -> dict[str, Any]:
        """Mark a word as known or unknown for a user"""
        return await self.progress_service.mark_word_known(user_id, word, language, is_known, db)

    async def bulk_mark_level(
        self, db: AsyncSession, user_id: int, language: str, level: str, is_known: bool
    ) -> dict[str, Any]:
        """Mark all words of a level as known or unknown"""
        return await self.progress_service.bulk_mark_level(db, user_id, language, level, is_known)

    async def get_user_vocabulary_stats(self, user_id: int, language: str, db: AsyncSession) -> dict[str, Any]:
        """Get vocabulary statistics for a user"""
        return await self.progress_service.get_user_vocabulary_stats(user_id, language, db)

    # ========== Stats Service Methods ==========

    async def get_vocabulary_stats(self, *args, **kwargs):
        """Get vocabulary statistics by level"""
        return await self.stats_service.get_vocabulary_stats(*args, **kwargs)

    async def get_user_progress_summary(self, db_session, user_id: str):
        """Get user's overall progress summary"""
        return await self.stats_service.get_user_progress_summary(db_session, user_id)

    async def get_supported_languages(self):
        """Get list of supported languages"""
        return await self.stats_service.get_supported_languages()

    async def extract_blocking_words_from_srt(
        self, db: AsyncSession, srt_content: str, user_id: int, video_path: str
    ) -> list[dict[str, Any]]:
        """Extract blocking words from SRT content for vocabulary learning"""
        try:
            import re

            # Parse SRT content to extract text
            blocks = re.split(r"\n\s*\n", srt_content.strip())
            all_text = []

            for block in blocks:
                lines = block.split("\n")
                if len(lines) >= 3:
                    # Skip the sequence number and timestamp lines
                    text_lines = lines[2:]
                    if text_lines:
                        all_text.append(" ".join(text_lines))

            # Combine all subtitle text
            full_text = " ".join(all_text)

            if not full_text.strip():
                return []

            # Extract German words from the text
            # Simple word extraction - in production this would use proper NLP
            german_words = re.findall(r"\b[A-Za-zäöüÄÖÜß]+(?:-[A-Za-zäöüÄÖÜß]+)*\b", full_text)

            # Filter out common words and short words
            filtered_words = [
                word.lower()
                for word in german_words
                if len(word) > 3
                and word.lower()
                not in {
                    "und",
                    "oder",
                    "der",
                    "die",
                    "das",
                    "ein",
                    "eine",
                    "einer",
                    "eines",
                    "den",
                    "dem",
                    "des",
                    "sie",
                    "wir",
                    "ihr",
                    "ich",
                    "du",
                    "er",
                    "es",
                    "ist",
                    "sind",
                    "war",
                    "waren",
                    "hat",
                    "haben",
                    "habe",
                    "mit",
                    "auf",
                    "aus",
                    "von",
                    "zu",
                    "für",
                    "durch",
                    "über",
                    "unter",
                    "vor",
                    "nach",
                    "bei",
                    "als",
                    "wie",
                    "was",
                    "wer",
                    "wo",
                    "wann",
                    "warum",
                    "viel",
                    "viele",
                    "wenig",
                    "wenige",
                    "mehr",
                    "weniger",
                    "am",
                    "im",
                    "um",
                    "an",
                    "in",
                    "ab",
                    "dann",
                    "also",
                    "aber",
                    "sondern",
                    "denn",
                    "doch",
                    "jedoch",
                    "nur",
                    "auch",
                    "noch",
                    "schon",
                    "bereits",
                    "immer",
                    "nie",
                    "oft",
                    "selten",
                    "manchmal",
                    "vielleicht",
                    "wahrscheinlich",
                    "sicher",
                    "bestimmt",
                }
            ]

            # Get unique words and create vocabulary entries
            unique_words = list(set(filtered_words))[:20]  # Limit to 20 words for testing

            blocking_words = []
            for word in unique_words:
                # Create a vocabulary entry matching the expected schema
                blocking_words.append(
                    {
                        "word": word,
                        "translation": f"Translation for {word}",  # Placeholder translation
                        "difficulty_level": "B1",  # Use difficulty_level not level
                        "lemma": word.lower(),
                        "concept_id": None,
                        "semantic_category": None,
                        "domain": None,
                        "known": False,
                    }
                )

            logger.info(f"Extracted {len(blocking_words)} blocking words from SRT content")
            return blocking_words

        except Exception as e:
            logger.error(f"Error extracting blocking words from SRT: {e}")
            return []


def get_vocabulary_service() -> VocabularyService:
    """Get vocabulary service instance - returns fresh instance to avoid global state"""
    return VocabularyService()
