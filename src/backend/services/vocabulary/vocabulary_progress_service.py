"""
Vocabulary Progress Service

User vocabulary progress tracking and bulk operations for language learning.
This module manages individual word progress, bulk level updates, and user statistics.

Key Components:
    - VocabularyProgressService: Main progress tracking service
    - Transactional word marking (known/unknown)
    - Bulk level operations (mark entire levels)
    - User statistics aggregation

Usage Example:
    ```python
    from services.vocabulary.vocabulary_progress_service import vocabulary_progress_service

    # Mark single word as known
    result = await vocabulary_progress_service.mark_word_known(
        user_id=123,
        word="Haus",
        language="de",
        is_known=True,
        db=db_session
    )

    # Mark entire level as known
    await vocabulary_progress_service.bulk_mark_level(
        db=db_session,
        user_id=123,
        language="de",
        level="A1",
        is_known=True
    )

    # Get user stats
    stats = await vocabulary_progress_service.get_user_vocabulary_stats(123, "de", db)
    ```

Dependencies:
    - sqlalchemy: Database operations and queries
    - database.models: UserVocabularyProgress, VocabularyWord

Thread Safety:
    Yes when using separate service instances per request.
    Singleton pattern used in production, per-test instances in testing.

Performance Notes:
    - Single word updates: O(1) with index on (user_id, vocabulary_id)
    - Bulk level updates: O(n) where n = words in level
    - Statistics: O(1) with proper indexes on joins
    - Uses transactional boundaries to ensure data consistency
"""

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger
from database.models import UserVocabularyProgress, VocabularyWord

logger = get_logger(__name__)


class VocabularyProgressService:
    """
    Service for tracking user vocabulary learning progress.

    Manages individual word progress (known/unknown status, confidence levels),
    bulk operations for entire difficulty levels, and user statistics.

    Attributes:
        query_service: Optional dependency on vocabulary query service for word lookups

    Example:
        ```python
        service = VocabularyProgressService()

        # Mark word as known (increases confidence)
        result = await service.mark_word_known(123, "Haus", "de", True, db)
        # result: {"success": True, "confidence_level": 2, ...}

        # Bulk mark level
        result = await service.bulk_mark_level(db, 123, "de", "A1", True)
        # result: {"success": True, "updated_count": 500, ...}

        # Get statistics
        stats = await service.get_user_vocabulary_stats(123, "de", db)
        # stats: {"total_words": 5000, "total_known": 1200, ...}
        ```

    Note:
        Transaction management handled by FastAPI dependency injection.
        Confidence levels: 0 (unknown) to 5 (very confident).
        Each review increments/decrements confidence.
    """

    def __init__(self, query_service=None):
        """Initialize with optional query service dependency"""
        self.query_service = query_service

    async def mark_word_known(
        self, user_id: int, word: str, language: str, is_known: bool, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Mark a word as known or unknown for a user

        Supports marking both:
        - Words in the vocabulary database (with vocabulary_id)
        - Unknown words not in the database (vocabulary_id = NULL, lemma-based)

        Transaction management handled by FastAPI session dependency
        """
        # Get word info from query service
        if not self.query_service:
            from .vocabulary_query_service import get_vocabulary_query_service

            self.query_service = get_vocabulary_query_service()

        word_info = await self.query_service.get_word_info(word, language, db)

        # Determine vocabulary_id and lemma
        if word_info.get("found"):
            # Word exists in vocabulary database
            vocab_id = word_info["id"]
            lemma = word_info["lemma"]
            difficulty_level = word_info["difficulty_level"]
        else:
            # Word not in vocabulary database - use lemmatization and allow marking as known
            from services.lemmatization_service import get_lemmatization_service

            # Lazy-load lemmatization service if needed
            if not hasattr(self, "lemmatization_service"):
                self.lemmatization_service = get_lemmatization_service()

            vocab_id = None  # No vocabulary_id for unknown words
            lemma = self.lemmatization_service.lemmatize(word)
            difficulty_level = "unknown"  # No CEFR level for unknown words

            logger.info("Marking unknown word", word=word, lemma=lemma, language=language)

        # Check existing progress by lemma (works for both known and unknown words)
        stmt = select(UserVocabularyProgress).where(
            and_(
                UserVocabularyProgress.user_id == user_id,
                UserVocabularyProgress.lemma == lemma,
                UserVocabularyProgress.language == language,
            )
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress:
            # Update existing progress
            progress.is_known = is_known
            if is_known:
                progress.confidence_level = min(progress.confidence_level + 1, 5)
            else:
                progress.confidence_level = max(progress.confidence_level - 1, 0)
            progress.review_count += 1
        else:
            # Create new progress
            progress = UserVocabularyProgress(
                user_id=user_id,
                vocabulary_id=vocab_id,  # May be NULL for unknown words
                lemma=lemma,
                language=language,
                is_known=is_known,
                confidence_level=1 if is_known else 0,
                review_count=1,
            )
            db.add(progress)

        # Capture values before commit (to avoid detached instance issues)
        result_data = {
            "success": True,
            "word": word,
            "lemma": lemma,
            "level": difficulty_level,
            "is_known": is_known,
            "confidence_level": progress.confidence_level,
        }

        await db.commit()  # Explicitly commit to persist changes

        return result_data

    async def bulk_mark_level(
        self, db: AsyncSession, user_id: int, language: str, level: str, is_known: bool
    ) -> dict[str, Any]:
        """
        Mark all words of a level as known or unknown
        Transaction management handled by FastAPI session dependency
        """
        # Get all words for the level
        stmt = select(VocabularyWord.id, VocabularyWord.lemma).where(
            and_(VocabularyWord.language == language, VocabularyWord.difficulty_level == level)
        )
        result = await db.execute(stmt)
        words = result.all()

        if not words:
            return {"success": True, "level": level, "language": language, "updated_count": 0, "is_known": is_known}

        vocab_ids = [vocab_id for vocab_id, _ in words]
        lemmas = [lemma for _, lemma in words]

        # Bulk get existing progress by lemma (matches unique constraint)
        existing_progress_stmt = select(UserVocabularyProgress).where(
            and_(
                UserVocabularyProgress.user_id == user_id,
                UserVocabularyProgress.lemma.in_(lemmas),
                UserVocabularyProgress.language == language,
            )
        )
        existing_result = await db.execute(existing_progress_stmt)
        existing_progress = {p.lemma: p for p in existing_result.scalars()}

        # Update or create progress records (deduplicate by lemma to handle duplicate words)
        new_progress_records = []
        processed_lemmas = set()  # Track lemmas we've already processed in this batch

        for vocab_id, lemma in words:
            if lemma in existing_progress:
                # Update existing progress record
                progress = existing_progress[lemma]
                progress.is_known = is_known
                progress.confidence_level = 3 if is_known else 0
                processed_lemmas.add(lemma)
            elif lemma not in processed_lemmas:
                # Create new progress record (only once per unique lemma)
                new_progress_records.append(
                    UserVocabularyProgress(
                        user_id=user_id,
                        vocabulary_id=vocab_id,
                        lemma=lemma,
                        language=language,
                        is_known=is_known,
                        confidence_level=3 if is_known else 0,
                        review_count=0,
                    )
                )
                processed_lemmas.add(lemma)

        if new_progress_records:
            db.add_all(new_progress_records)

        await db.commit()  # Explicitly commit to persist all changes

        return {
            "success": True,
            "level": level,
            "language": language,
            "updated_count": len(words),
            "is_known": is_known,
        }

    async def get_user_vocabulary_stats(self, user_id: int, language: str, db: AsyncSession) -> dict[str, Any]:
        """Get vocabulary statistics for a user"""
        # Total words in language
        total_stmt = select(func.count(VocabularyWord.id)).where(VocabularyWord.language == language)
        total_result = await db.execute(total_stmt)
        total_words = total_result.scalar() or 0

        # Known words by user
        known_stmt = select(func.count(UserVocabularyProgress.id)).where(
            and_(
                UserVocabularyProgress.user_id == user_id,
                UserVocabularyProgress.language == language,
                UserVocabularyProgress.is_known,
            )
        )
        known_result = await db.execute(known_stmt)
        known_words = known_result.scalar() or 0

        # Words by level
        level_stmt = (
            select(
                VocabularyWord.difficulty_level,
                func.count(VocabularyWord.id).label("total"),
                func.count(UserVocabularyProgress.id).label("known"),
            )
            .outerjoin(
                UserVocabularyProgress,
                and_(
                    UserVocabularyProgress.vocabulary_id == VocabularyWord.id,
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.is_known,
                ),
            )
            .where(VocabularyWord.language == language)
            .group_by(VocabularyWord.difficulty_level)
        )
        level_result = await db.execute(level_stmt)

        words_by_level = {}
        for row in level_result:
            level, total, known = row
            words_by_level[level] = {
                "total": total,
                "known": known or 0,
                "percentage": round((known or 0) / total * 100, 1) if total > 0 else 0,
            }

        return {
            "total_words": total_words,
            "total_known": known_words,
            "percentage_known": round(known_words / total_words * 100, 1) if total_words > 0 else 0,
            "words_by_level": words_by_level,
            "language": language,
        }


# Test-aware singleton pattern
def get_vocabulary_progress_service() -> VocabularyProgressService:
    """
    Get vocabulary progress service instance.

    Always returns a new instance to eliminate global state.
    Services are stateless, so recreation is cheap and prevents test pollution.
    """
    return VocabularyProgressService()
