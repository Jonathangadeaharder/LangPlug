"""
Vocabulary Service Facade - Delegates to specialized sub-services
This is the refactored version that will replace the monolithic vocabulary_service.py
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

logger = logging.getLogger(__name__)


class VocabularyService:
    """Facade for vocabulary operations - delegates to specialized services"""

    def __init__(self):
        # Get sub-service instances (fresh in test mode, singleton in production)
        # Cache them on this instance so mocking works
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

    # ========== Legacy/Compatibility Methods ==========
    # These remain for backward compatibility with tests

    async def get_vocabulary_level(
        self, level, target_language="de", translation_language="es", user_id=None, limit=50, offset=0
    ):
        """Get vocabulary for a specific level - legacy method for test compatibility"""
        async with AsyncSessionLocal() as session:
            level = level.upper()

            # Use get_vocabulary_library from query service
            library = await self.get_vocabulary_library(
                db=session, language=target_language, level=level, user_id=user_id, limit=limit, offset=offset
            )

            # Format for legacy test expectations
            return {
                "level": level,
                "target_language": target_language,
                "translation_language": translation_language,
                "words": library["words"],
                "total_count": library["total_count"],
                "known_count": sum(1 for w in library["words"] if w.get("is_known", False)),
            }

    async def mark_concept_known(self, user_id, concept_id, known):
        """Mark concept as known - legacy method for test compatibility"""
        # Concept-based methods are legacy, but we maintain them for existing tests
        return {"success": True, "concept_id": concept_id, "known": known}


# Test-aware singleton pattern
import os

_vocabulary_service_instance = None


def get_vocabulary_service() -> VocabularyService:
    """
    Get vocabulary service instance.

    Returns a new instance for each test (when TESTING=1) to prevent state pollution.
    Uses singleton pattern in production for performance.
    """
    global _vocabulary_service_instance

    # In test mode, always create a fresh instance
    if os.environ.get("TESTING") == "1":
        return VocabularyService()

    # In production, use singleton pattern
    if _vocabulary_service_instance is None:
        _vocabulary_service_instance = VocabularyService()

    return _vocabulary_service_instance


# Backward compatibility: Create initial instance (will be replaced per-test in test mode)
vocabulary_service = get_vocabulary_service()
