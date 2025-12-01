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

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.config.language_config import MIN_WORD_LENGTH, filter_stopwords
from core.config.logging_config import get_logger
from core.database import AsyncSessionLocal

logger = get_logger(__name__)

# Default limit for extracted vocabulary words
DEFAULT_VOCAB_EXTRACT_LIMIT = 20


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
        # Use via dependency injection
        @router.get("/word/{word}")
        async def get_word(
            word: str,
            db: AsyncSession = Depends(get_async_session),
            vocab_service = Depends(get_vocabulary_service)
        ):
            return await vocab_service.get_word_info(word, "de", db)
        ```

    Note:
        Dependencies are injected to allow proper testing and mocking.
    """

    def __init__(self, query_service, progress_service, stats_service):
        """
        Initialize with injected dependencies.

        Args:
            query_service: Service for word lookups
            progress_service: Service for progress tracking
            stats_service: Service for statistics
        """
        self.query_service = query_service
        self.progress_service = progress_service
        self.stats_service = stats_service

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
        self,
        db: AsyncSession,
        srt_content: str,
        user_id: int,
        video_path: str,
        language: str = "de",
        limit: int = DEFAULT_VOCAB_EXTRACT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Extract blocking words from SRT content for vocabulary learning.

        Args:
            db: Database session
            srt_content: Raw SRT subtitle content
            user_id: User ID for filtering known words
            video_path: Path to the video file
            language: ISO 639-1 language code (default: 'de' for German)
            limit: Maximum number of words to return

        Returns:
            List of vocabulary word dictionaries with word info
        """
        try:
            # Extract text from SRT blocks
            full_text = self._extract_text_from_srt(srt_content)
            if not full_text.strip():
                return []

            # Extract words matching the target language pattern
            raw_words = self._extract_words_from_text(full_text, language)

            # Filter out stopwords and short words using centralized config
            filtered_words = [word.lower() for word in raw_words if len(word) >= MIN_WORD_LENGTH]
            filtered_words = filter_stopwords(filtered_words, language)

            # Get unique words and create vocabulary entries
            unique_words = list(set(filtered_words))[:limit]

            blocking_words = [self._create_vocabulary_entry(word, language) for word in unique_words]

            logger.debug("Extracted blocking words from SRT", count=len(blocking_words))
            return blocking_words

        except Exception as e:
            logger.error("Error extracting blocking words from SRT", error=str(e))
            return []

    def _extract_text_from_srt(self, srt_content: str) -> str:
        """Extract plain text from SRT subtitle content."""
        blocks = re.split(r"\n\s*\n", srt_content.strip())
        all_text = []

        for block in blocks:
            lines = block.split("\n")
            if len(lines) >= 3:
                # Skip the sequence number and timestamp lines
                text_lines = lines[2:]
                if text_lines:
                    all_text.append(" ".join(text_lines))

        return " ".join(all_text)

    def _extract_words_from_text(self, text: str, language: str) -> list[str]:
        """Extract words from text based on language-specific patterns."""
        # Pattern includes German umlauts and compound words with hyphens
        if language == "de":
            pattern = r"\b[A-Za-zäöüÄÖÜß]+(?:-[A-Za-zäöüÄÖÜß]+)*\b"
        elif language == "es":
            pattern = r"\b[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+(?:-[A-Za-záéíóúüñÁÉÍÓÚÜÑ]+)*\b"
        else:
            # Default pattern for English and other Latin-script languages
            pattern = r"\b[A-Za-z]+(?:-[A-Za-z]+)*\b"

        return re.findall(pattern, text)

    def _create_vocabulary_entry(self, word: str, language: str) -> dict[str, Any]:
        """Create a vocabulary entry dictionary for a word."""
        return {
            "word": word,
            "translation": f"Translation for {word}",
            "difficulty_level": "B1",
            "lemma": word.lower(),
            "language": language,
            "concept_id": None,
            "semantic_category": None,
            "domain": None,
            "known": False,
        }


def get_vocabulary_service(query_service, progress_service, stats_service) -> VocabularyService:
    """Factory function with dependency injection"""
    return VocabularyService(query_service, progress_service, stats_service)
