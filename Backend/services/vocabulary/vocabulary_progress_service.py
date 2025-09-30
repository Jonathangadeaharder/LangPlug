"""
Vocabulary Progress Service - Handles user progress tracking
"""

import logging
from typing import Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import VocabularyWord, UserVocabularyProgress

logger = logging.getLogger(__name__)


class VocabularyProgressService:
    """Handles user vocabulary progress tracking and bulk operations"""

    def __init__(self, query_service=None):
        """Initialize with optional query service dependency"""
        self.query_service = query_service

    async def mark_word_known(
        self,
        user_id: int,
        word: str,
        language: str,
        is_known: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Mark a word as known or unknown for a user"""
        # Get word info from query service
        if not self.query_service:
            from .vocabulary_query_service import vocabulary_query_service
            self.query_service = vocabulary_query_service

        word_info = await self.query_service.get_word_info(word, language, db)

        if not word_info.get("found"):
            return {
                "success": False,
                "message": "Word not in vocabulary database",
                "word": word,
                "lemma": word_info.get("lemma")
            }

        vocab_id = word_info["id"]
        lemma = word_info["lemma"]

        # Check existing progress
        stmt = (
            select(UserVocabularyProgress)
            .where(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.vocabulary_id == vocab_id
                )
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
                vocabulary_id=vocab_id,
                lemma=lemma,
                language=language,
                is_known=is_known,
                confidence_level=1 if is_known else 0,
                review_count=1
            )
            db.add(progress)

        await db.commit()

        return {
            "success": True,
            "word": word,
            "lemma": lemma,
            "level": word_info["difficulty_level"],
            "is_known": is_known,
            "confidence_level": progress.confidence_level
        }

    async def bulk_mark_level(
        self,
        db: AsyncSession,
        user_id: int,
        language: str,
        level: str,
        is_known: bool
    ) -> Dict[str, Any]:
        """Mark all words of a level as known or unknown"""
        # Get all words for the level
        stmt = (
            select(VocabularyWord.id, VocabularyWord.lemma)
            .where(
                and_(
                    VocabularyWord.language == language,
                    VocabularyWord.difficulty_level == level
                )
            )
        )
        result = await db.execute(stmt)
        words = result.all()

        if not words:
            return {"success": True, "level": level, "language": language,
                    "updated_count": 0, "is_known": is_known}

        vocab_ids = [vocab_id for vocab_id, _ in words]

        # Bulk get existing progress
        existing_progress_stmt = (
            select(UserVocabularyProgress)
            .where(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.vocabulary_id.in_(vocab_ids)
                )
            )
        )
        existing_result = await db.execute(existing_progress_stmt)
        existing_progress = {p.vocabulary_id: p for p in existing_result.scalars()}

        # Update or create progress records
        new_progress_records = []
        for vocab_id, lemma in words:
            if vocab_id in existing_progress:
                progress = existing_progress[vocab_id]
                progress.is_known = is_known
                progress.confidence_level = 3 if is_known else 0
            else:
                new_progress_records.append(UserVocabularyProgress(
                    user_id=user_id,
                    vocabulary_id=vocab_id,
                    lemma=lemma,
                    language=language,
                    is_known=is_known,
                    confidence_level=3 if is_known else 0,
                    review_count=0
                ))

        if new_progress_records:
            db.add_all(new_progress_records)

        await db.commit()

        return {
            "success": True,
            "level": level,
            "language": language,
            "updated_count": len(words),
            "is_known": is_known
        }

    async def get_user_vocabulary_stats(
        self,
        user_id: int,
        language: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get vocabulary statistics for a user"""
        # Total words in language
        total_stmt = (
            select(func.count(VocabularyWord.id))
            .where(VocabularyWord.language == language)
        )
        total_result = await db.execute(total_stmt)
        total_words = total_result.scalar() or 0

        # Known words by user
        known_stmt = (
            select(func.count(UserVocabularyProgress.id))
            .where(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.language == language,
                    UserVocabularyProgress.is_known == True
                )
            )
        )
        known_result = await db.execute(known_stmt)
        known_words = known_result.scalar() or 0

        # Words by level
        level_stmt = (
            select(
                VocabularyWord.difficulty_level,
                func.count(VocabularyWord.id).label('total'),
                func.count(UserVocabularyProgress.id).label('known')
            )
            .outerjoin(
                UserVocabularyProgress,
                and_(
                    UserVocabularyProgress.vocabulary_id == VocabularyWord.id,
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.is_known == True
                )
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
                "percentage": round((known or 0) / total * 100, 1) if total > 0 else 0
            }

        return {
            "total_words": total_words,
            "total_known": known_words,
            "percentage_known": round(known_words / total_words * 100, 1) if total_words > 0 else 0,
            "words_by_level": words_by_level,
            "language": language
        }


# Global instance
vocabulary_progress_service = VocabularyProgressService()


def get_vocabulary_progress_service() -> VocabularyProgressService:
    """Get vocabulary progress service instance"""
    return vocabulary_progress_service
