"""
Repository for user vocabulary progress operations using domain entities
"""

from datetime import datetime

from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import Session

from database.models import UserVocabularyProgress as ProgressModel
from database.models import VocabularyWord as VocabularyWordModel
from database.repositories.base_repository_sync import BaseSyncRepository
from database.repositories.interfaces import UserVocabularyProgressRepositoryInterface
from domains.vocabulary.entities import ConfidenceLevel, UserVocabularyProgress, VocabularyWord


class UserVocabularyProgressRepository(
    BaseSyncRepository[ProgressModel, int], UserVocabularyProgressRepositoryInterface
):
    """Repository for user vocabulary progress operations using domain entities"""

    def __init__(self):
        super().__init__(ProgressModel)

    async def get_user_progress(self, db: Session, user_id: int, language: str = "de") -> list[UserVocabularyProgress]:
        """Get all vocabulary progress for a user"""
        return (
            db.query(UserVocabularyProgress)
            .filter(and_(UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.language == language))
            .all()
        )

    async def get_user_word_progress(
        self, db: Session, user_id: int, vocabulary_id: int
    ) -> UserVocabularyProgress | None:
        """Get specific word progress for user"""
        return (
            db.query(UserVocabularyProgress)
            .filter(
                and_(UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.vocabulary_id == vocabulary_id)
            )
            .first()
        )

    async def mark_word_known(
        self, db: Session, user_id: int, vocabulary_id: int, is_known: bool
    ) -> UserVocabularyProgress:
        """Mark word as known/unknown for user"""
        progress = await self.get_user_word_progress(db, user_id, vocabulary_id)

        if progress:
            progress.is_known = is_known
            progress.last_reviewed_at = datetime.utcnow()
            progress.review_count += 1
        else:
            # Get vocabulary word to extract lemma and language
            vocab_word = db.query(VocabularyWord).filter(VocabularyWord.id == vocabulary_id).first()
            if not vocab_word:
                raise ValueError(f"Vocabulary word with id {vocabulary_id} not found")

            progress = UserVocabularyProgress(
                user_id=user_id,
                vocabulary_id=vocabulary_id,
                lemma=vocab_word.lemma,
                language=vocab_word.language,
                is_known=is_known,
                review_count=1,
                last_reviewed_at=datetime.utcnow(),
            )
            db.add(progress)

        db.commit()
        db.refresh(progress)
        return progress

    async def get_user_known_words(
        self, db: Session, user_id: int, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[UserVocabularyProgress]:
        """Get user's known words"""
        return (
            db.query(UserVocabularyProgress)
            .filter(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.language == language,
                    UserVocabularyProgress.is_known,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def get_user_unknown_words(
        self, db: Session, user_id: int, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[UserVocabularyProgress]:
        """Get user's unknown words"""
        return (
            db.query(UserVocabularyProgress)
            .filter(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.language == language,
                    not UserVocabularyProgress.is_known,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def get_vocabulary_stats(self, db: Session, user_id: int, language: str = "de") -> dict:
        """Get vocabulary statistics for user"""
        total_progress = (
            db.query(func.count(UserVocabularyProgress.id))
            .filter(and_(UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.language == language))
            .scalar()
        )

        known_count = (
            db.query(func.count(UserVocabularyProgress.id))
            .filter(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.language == language,
                    UserVocabularyProgress.is_known,
                )
            )
            .scalar()
        )

        unknown_count = total_progress - known_count

        return {
            "total_reviewed": total_progress,
            "known_words": known_count,
            "unknown_words": unknown_count,
            "percentage_known": round((known_count / total_progress * 100), 2) if total_progress > 0 else 0,
        }

    async def bulk_mark_words(
        self, db: Session, user_id: int, vocabulary_ids: list[int], is_known: bool
    ) -> list[UserVocabularyProgress]:
        """Bulk mark multiple words as known/unknown - optimized version"""
        if not vocabulary_ids:
            return []

        # Step 1: Get existing progress for all vocabulary_ids
        existing_stmt = select(UserVocabularyProgress).where(
            and_(UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.vocabulary_id.in_(vocabulary_ids))
        )
        existing_result = db.execute(existing_stmt)
        existing_progress = {p.vocabulary_id: p for p in existing_result.scalars()}

        # Step 2: Bulk update existing records
        existing_ids = list(existing_progress.keys())
        if existing_ids:
            update_stmt = (
                update(UserVocabularyProgress)
                .where(
                    and_(
                        UserVocabularyProgress.user_id == user_id,
                        UserVocabularyProgress.vocabulary_id.in_(existing_ids),
                    )
                )
                .values(
                    is_known=is_known,
                    last_reviewed_at=datetime.utcnow(),
                    review_count=UserVocabularyProgress.review_count + 1,
                )
            )
            db.execute(update_stmt)

        # Step 3: Bulk insert new records
        new_vocab_ids = [vid for vid in vocabulary_ids if vid not in existing_progress]
        new_records = []
        if new_vocab_ids:
            # Get vocabulary details for new records
            vocab_stmt = select(VocabularyWord).where(VocabularyWord.id.in_(new_vocab_ids))
            vocab_result = db.execute(vocab_stmt)
            vocab_words = {v.id: v for v in vocab_result.scalars()}

            for vocab_id in new_vocab_ids:
                vocab_word = vocab_words.get(vocab_id)
                if vocab_word:
                    new_records.append(
                        UserVocabularyProgress(
                            user_id=user_id,
                            vocabulary_id=vocab_id,
                            lemma=vocab_word.lemma,
                            language=vocab_word.language,
                            is_known=is_known,
                            review_count=1,
                            last_reviewed_at=datetime.utcnow(),
                        )
                    )

            if new_records:
                db.add_all(new_records)

        db.commit()

        # Return updated records
        final_stmt = select(UserVocabularyProgress).where(
            and_(UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.vocabulary_id.in_(vocabulary_ids))
        )
        final_result = db.execute(final_stmt)
        models = final_result.scalars().all()
        return [
            self._to_domain_entity(model, vocab_words.get(model.vocabulary_id))
            for model in models
            if vocab_words.get(model.vocabulary_id)
        ]

    def _to_domain_entity(self, model: ProgressModel, vocab_word: VocabularyWordModel = None) -> UserVocabularyProgress:
        """Convert database model to domain entity"""
        # Import vocabulary repository to get vocabulary word if needed
        if not vocab_word and model.vocabulary_id:
            from .vocabulary_repository import VocabularyRepository

            vocab_repo = VocabularyRepository()
            # This would need proper session handling in real implementation
            vocab_word = vocab_repo._to_domain_entity(model.vocabulary)

        # Convert confidence level
        try:
            confidence_level = ConfidenceLevel(getattr(model, "confidence_level", 0))
        except (ValueError, AttributeError):
            confidence_level = ConfidenceLevel.UNKNOWN

        return UserVocabularyProgress(
            id=model.id,
            user_id=model.user_id,
            vocabulary_word=vocab_word,
            is_known=model.is_known,
            confidence_level=confidence_level,
            review_count=getattr(model, "review_count", 0),
            correct_count=getattr(model, "correct_count", 0),
            incorrect_count=getattr(model, "incorrect_count", 0),
            first_learned_at=getattr(model, "first_learned_at", None),
            last_reviewed_at=getattr(model, "last_reviewed_at", None),
            next_review_at=getattr(model, "next_review_at", None),
            difficulty_adjustment=getattr(model, "difficulty_adjustment", 1.0),
            learning_streak=getattr(model, "learning_streak", 0),
            notes=getattr(model, "notes", None),
        )
