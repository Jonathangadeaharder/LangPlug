"""
Vocabulary Lookup Service - Handles word lookups and basic queries
Extracted from vocabulary_service.py for better separation of concerns
"""

import logging
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UnknownWord, VocabularyWord
from services.interfaces.base import IService
from services.lemmatization_service import lemmatization_service

logger = logging.getLogger(__name__)


class VocabularyLookupService(IService):
    """Service responsible for vocabulary word lookups and searches"""

    async def get_word_info(self, word: str, language: str, db: AsyncSession) -> dict[str, Any] | None:
        """Get vocabulary information for a word"""
        # First try lemmatization
        lemma = lemmatization_service.lemmatize(word)

        # Look up by lemma first, then by exact word
        stmt = (
            select(VocabularyWord)
            .where(
                and_(
                    or_(
                        func.lower(VocabularyWord.lemma) == lemma.lower(),
                        func.lower(VocabularyWord.word) == word.lower(),
                    ),
                    VocabularyWord.language == language,
                )
            )
            .limit(1)
        )

        result = await db.execute(stmt)
        vocab_word = result.scalar_one_or_none()

        if vocab_word:
            return {
                "id": vocab_word.id,
                "word": word,
                "lemma": vocab_word.lemma,
                "found_word": vocab_word.word,
                "language": vocab_word.language,
                "difficulty_level": vocab_word.difficulty_level,
                "part_of_speech": vocab_word.part_of_speech,
                "gender": vocab_word.gender,
                "translation_en": vocab_word.translation_en,
                "pronunciation": vocab_word.pronunciation,
                "notes": vocab_word.notes,
                "found": True,
            }

        # Word not found - track it
        await self._track_unknown_word(word, lemma, language, db)

        return {
            "word": word,
            "lemma": lemma,
            "language": language,
            "found": False,
            "message": "Word not in vocabulary database",
        }

    async def search_vocabulary(
        self, db: AsyncSession, search_term: str, language: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search vocabulary by word or lemma"""
        search_lower = search_term.lower()

        stmt = (
            select(VocabularyWord)
            .where(
                and_(
                    or_(
                        func.lower(VocabularyWord.word).like(f"%{search_lower}%"),
                        func.lower(VocabularyWord.lemma).like(f"%{search_lower}%"),
                    ),
                    VocabularyWord.language == language,
                )
            )
            .order_by(
                # Exact matches first
                func.lower(VocabularyWord.word) == search_lower,
                func.lower(VocabularyWord.lemma) == search_lower,
                # Then by difficulty and frequency
                VocabularyWord.difficulty_level,
                VocabularyWord.frequency_rank.nullslast(),
            )
            .limit(limit)
        )

        result = await db.execute(stmt)
        words = result.scalars().all()

        return [
            {
                "id": word.id,
                "word": word.word,
                "lemma": word.lemma,
                "difficulty_level": word.difficulty_level,
                "part_of_speech": word.part_of_speech,
                "translation_en": word.translation_en,
            }
            for word in words
        ]

    async def get_vocabulary_library(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        language: str = "de",
        level: str | None = None,
        known_filter: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Get vocabulary library with optional filtering"""
        # Base query
        query = select(VocabularyWord).where(VocabularyWord.language == language)

        # Filter by level if specified
        if level:
            query = query.where(VocabularyWord.difficulty_level == level)

        # Order by frequency rank or difficulty
        query = query.order_by(
            VocabularyWord.difficulty_level, VocabularyWord.frequency_rank.nullslast(), VocabularyWord.lemma
        )

        # Get total count
        count_stmt = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.limit(per_page).offset(offset)

        # Execute query
        result = await db.execute(query)
        words = result.scalars().all()

        # Format response
        word_list = []
        for word in words:
            word_data = {
                "id": word.id,
                "word": word.word,
                "lemma": word.lemma,
                "difficulty_level": word.difficulty_level,
                "part_of_speech": word.part_of_speech,
                "gender": word.gender,
                "translation_en": word.translation_en,
                "pronunciation": word.pronunciation,
            }
            word_list.append(word_data)

        return {
            "words": word_list,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "language": language,
            "level": level,
        }

    async def get_vocabulary_level(
        self,
        db: AsyncSession,
        level: str,
        target_language: str = "de",
        translation_language: str = "es",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get vocabulary for a specific level"""
        level = level.upper()  # Normalize to uppercase

        stmt = (
            select(VocabularyWord)
            .where(and_(VocabularyWord.difficulty_level == level, VocabularyWord.language == target_language))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        words = result.scalars().all()

        # Process words into response format
        word_list = []
        for word in words:
            word_data = {
                "concept_id": word.id,
                "word": word.word,
                "translation": word.translation_en or "",
                "gender": word.gender or "",
                "plural_form": "",
                "pronunciation": word.pronunciation or "",
                "notes": word.notes or "",
                "known": False,
            }
            word_list.append(word_data)

        return {
            "level": level,
            "target_language": target_language,
            "translation_language": translation_language,
            "words": word_list,
            "known_count": 0,
        }

    def validate_language_code(self, language_code: str) -> bool:
        """Validate if a language code is supported"""
        if not language_code or not isinstance(language_code, str):
            return False

        supported_languages = ["de", "en", "es", "fr", "it", "pt", "nl", "sv", "da", "no"]
        return language_code.lower() in supported_languages

    def calculate_difficulty_score(self, level: str) -> int:
        """Calculate numeric difficulty score from CEFR level"""
        level_scores = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
        return level_scores.get(level, 0)

    async def _track_unknown_word(self, word: str, lemma: str, language: str, db: AsyncSession):
        """Track words not in vocabulary database"""
        stmt = select(UnknownWord).where(and_(UnknownWord.word == word, UnknownWord.language == language))
        result = await db.execute(stmt)
        unknown = result.scalar_one_or_none()

        if unknown:
            unknown.frequency_count += 1
            unknown.last_encountered = func.now()
        else:
            unknown = UnknownWord(word=word, lemma=lemma, language=language, frequency_count=1)
            db.add(unknown)

        try:
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to track unknown word: {e}")
            await db.rollback()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the vocabulary lookup service"""
        return {"service": "VocabularyLookupService", "status": "healthy", "lemmatization": "available"}

    async def initialize(self) -> None:
        """Initialize vocabulary lookup service resources"""
        logger.info("VocabularyLookupService initialized")

    async def cleanup(self) -> None:
        """Cleanup vocabulary lookup service resources"""
        logger.info("VocabularyLookupService cleanup completed")

    async def get_vocabulary_stats(
        self, db: AsyncSession, user_id: int | None = None, language: str = "de"
    ) -> dict[str, Any]:
        """Get vocabulary statistics"""
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        stats = {"language": language, "levels": {}, "total_words": 0}

        for level in levels:
            # Count total words at this level
            total_stmt = select(func.count(VocabularyWord.id)).where(
                and_(VocabularyWord.language == language, VocabularyWord.difficulty_level == level)
            )
            total_result = await db.execute(total_stmt)
            total_count = total_result.scalar() or 0

            stats["levels"][level] = {"total_words": total_count}
            stats["total_words"] += total_count

        return stats
