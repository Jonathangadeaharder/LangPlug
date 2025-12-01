"""
Vocabulary Query Service - Handles vocabulary lookups and searches
"""

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger
from database.models import UnknownWord, UserVocabularyProgress, VocabularyWord
from services.lemmatization_service import get_lemmatization_service

logger = get_logger(__name__)


class VocabularyQueryService:
    """Handles vocabulary queries, searches, and library operations"""

    def __init__(self):
        self.lemmatization_service = get_lemmatization_service()

    def _build_vocabulary_query(self, language: str, level: str | None = None):
        """Build base vocabulary query with filters and ordering

        Args:
            language: Language code to filter by
            level: Optional difficulty level to filter by (A1-C2)

        Returns:
            SQLAlchemy select query
        """
        query = select(VocabularyWord).where(VocabularyWord.language == language)

        if level:
            query = query.where(VocabularyWord.difficulty_level == level)

        return query.order_by(
            VocabularyWord.difficulty_level, VocabularyWord.frequency_rank.nullslast(), VocabularyWord.lemma
        )

    async def _count_query_results(self, db: AsyncSession, query) -> int:
        """Count total results for a query

        Args:
            db: Database session
            query: SQLAlchemy select query

        Returns:
            Total count of results
        """
        count_stmt = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_stmt)
        return count_result.scalar() or 0

    async def _execute_paginated_query(self, db: AsyncSession, query, limit: int, offset: int) -> list[VocabularyWord]:
        """Execute query with pagination

        Args:
            db: Database session
            query: SQLAlchemy select query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of VocabularyWord objects
        """
        paginated_query = query.limit(limit).offset(offset)
        result = await db.execute(paginated_query)
        return result.scalars().all()

    async def _get_user_progress_map(
        self, db: AsyncSession, user_id: int, words: list[VocabularyWord]
    ) -> dict[int, dict[str, Any]]:
        """Fetch user progress for vocabulary words by matching lemmas

        Args:
            db: Database session
            user_id: User ID to fetch progress for
            words: List of VocabularyWord objects

        Returns:
            Dictionary mapping vocabulary_id to progress data
        """
        if not words:
            return {}

        # Query by lemma to match the unique constraint and bulk_mark_level behavior
        lemmas = [w.lemma for w in words]
        language = words[0].language if words else "de"

        logger.debug("Fetching progress", user_id=user_id, language=language, lemma_count=len(lemmas))

        progress_stmt = select(UserVocabularyProgress).where(
            and_(
                UserVocabularyProgress.user_id == user_id,
                UserVocabularyProgress.lemma.in_(lemmas),
                UserVocabularyProgress.language == language,
            )
        )
        progress_result = await db.execute(progress_stmt)

        # Create map from lemma to progress
        lemma_to_progress = {
            p.lemma: {"is_known": p.is_known, "confidence_level": p.confidence_level} for p in progress_result.scalars()
        }

        logger.debug("Found progress", lemma_count=len(lemma_to_progress))

        # Map back to vocabulary_id using words list
        result_map = {word.id: lemma_to_progress[word.lemma] for word in words if word.lemma in lemma_to_progress}

        logger.debug("Mapped progress", vocab_id_count=len(result_map))

        return result_map

    def _format_vocabulary_word(
        self, word: VocabularyWord, user_progress: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Format single vocabulary word with optional user progress

        Args:
            word: VocabularyWord object
            user_progress: Optional user progress data

        Returns:
            Formatted word dictionary
        """
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

        if user_progress:
            word_data.update(user_progress)
        else:
            word_data["is_known"] = False
            word_data["confidence_level"] = 0

        return word_data

    async def _track_unknown_word(self, word: str, lemma: str, language: str, db: AsyncSession):
        """
        Track words not in vocabulary database

        Note: This method is called from within @transactional decorated functions,
        so it uses flush() instead of commit(). The transaction will be committed
        by the decorator.
        """
        try:
            stmt = select(UnknownWord).where(and_(UnknownWord.word == word, UnknownWord.language == language))
            result = await db.execute(stmt)
            unknown = result.scalar_one_or_none()

            if unknown:
                unknown.frequency_count += 1
                unknown.last_encountered = func.now()
            else:
                unknown = UnknownWord(word=word, lemma=lemma, language=language, frequency_count=1)
                db.add(unknown)

            # Flush to database but don't commit - let the @transactional decorator handle that
            await db.flush()
        except Exception as e:
            # Log the error but don't rollback - let the decorator handle it
            logger.warning("Failed to track unknown word", word=word, error=str(e))

    async def get_word_info(self, word: str, language: str, db: AsyncSession) -> dict[str, Any] | None:
        """Get vocabulary information for a word"""
        # First try lemmatization
        lemma = self.lemmatization_service.lemmatize(word)

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
        # Build and execute query
        query = self._build_vocabulary_query(language, level)
        total_count = await self._count_query_results(db, query)
        words = await self._execute_paginated_query(db, query, limit, offset)

        # Get user progress if needed
        progress_map = {}
        if user_id:
            progress_map = await self._get_user_progress_map(db, user_id, words)

        # Format response
        word_list = [self._format_vocabulary_word(word, progress_map.get(word.id)) for word in words]

        return {
            "words": word_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "language": language,
            "level": level,
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


# Test-aware singleton pattern
def get_vocabulary_query_service() -> VocabularyQueryService:
    """
    Get vocabulary query service instance.

    Always returns a new instance to eliminate global state.
    Services are stateless, so recreation is cheap and prevents test pollution.
    """
    return VocabularyQueryService()
