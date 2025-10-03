"""
Vocabulary domain services
"""

from sqlalchemy.orm import Session

from database.repositories.interfaces import UserVocabularyProgressRepositoryInterface, VocabularyRepositoryInterface

from .models import (
    BulkMarkWordsRequest,
    MarkWordRequest,
    UserVocabularyProgressResponse,
    VocabularyStatsResponse,
    VocabularyWordResponse,
)


class VocabularyService:
    """Service for vocabulary operations"""

    def __init__(
        self,
        vocabulary_repository: VocabularyRepositoryInterface,
        progress_repository: UserVocabularyProgressRepositoryInterface,
    ):
        self.vocabulary_repository = vocabulary_repository
        self.progress_repository = progress_repository

    async def search_words(
        self, db: Session, query: str, language: str = "de", limit: int = 20
    ) -> list[VocabularyWordResponse]:
        """Search vocabulary words"""
        words = await self.vocabulary_repository.search_words(db, query, language, limit)
        return [VocabularyWordResponse.from_orm(word) for word in words]

    async def get_words_by_level(
        self, db: Session, level: str, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[VocabularyWordResponse]:
        """Get vocabulary words by difficulty level"""
        words = await self.vocabulary_repository.get_by_difficulty_level(db, level, language, skip, limit)
        return [VocabularyWordResponse.from_orm(word) for word in words]

    async def get_word_by_lemma(self, db: Session, lemma: str, language: str = "de") -> VocabularyWordResponse | None:
        """Get vocabulary word by lemma"""
        word = await self.vocabulary_repository.get_by_lemma(db, lemma, language)
        return VocabularyWordResponse.from_orm(word) if word else None

    async def get_random_words(
        self, db: Session, language: str = "de", difficulty_levels: list[str] | None = None, limit: int = 10
    ) -> list[VocabularyWordResponse]:
        """Get random vocabulary words"""
        words = await self.vocabulary_repository.get_random_words(db, language, difficulty_levels, limit)
        return [VocabularyWordResponse.from_orm(word) for word in words]

    async def mark_word_known(
        self, db: Session, user_id: int, request: MarkWordRequest
    ) -> UserVocabularyProgressResponse:
        """Mark word as known/unknown for user"""
        progress = await self.progress_repository.mark_word_known(db, user_id, request.vocabulary_id, request.is_known)
        return UserVocabularyProgressResponse.from_orm(progress)

    async def bulk_mark_words(
        self, db: Session, user_id: int, request: BulkMarkWordsRequest
    ) -> list[UserVocabularyProgressResponse]:
        """Bulk mark multiple words as known/unknown"""
        progress_list = await self.progress_repository.bulk_mark_words(
            db, user_id, request.vocabulary_ids, request.is_known
        )
        return [UserVocabularyProgressResponse.from_orm(progress) for progress in progress_list]

    async def get_user_progress(
        self, db: Session, user_id: int, language: str = "de"
    ) -> list[UserVocabularyProgressResponse]:
        """Get user's vocabulary progress"""
        progress_list = await self.progress_repository.get_user_progress(db, user_id, language)
        return [UserVocabularyProgressResponse.from_orm(progress) for progress in progress_list]

    async def get_user_known_words(
        self, db: Session, user_id: int, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[UserVocabularyProgressResponse]:
        """Get user's known words"""
        known_words = await self.progress_repository.get_user_known_words(db, user_id, language, skip, limit)
        return [UserVocabularyProgressResponse.from_orm(word) for word in known_words]

    async def get_user_unknown_words(
        self, db: Session, user_id: int, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[UserVocabularyProgressResponse]:
        """Get user's unknown words"""
        unknown_words = await self.progress_repository.get_user_unknown_words(db, user_id, language, skip, limit)
        return [UserVocabularyProgressResponse.from_orm(word) for word in unknown_words]

    async def get_vocabulary_stats(self, db: Session, user_id: int, language: str = "de") -> VocabularyStatsResponse:
        """Get vocabulary statistics for user"""
        stats = await self.progress_repository.get_vocabulary_stats(db, user_id, language)

        level_breakdown = await self.vocabulary_repository.count_by_difficulty(db, language)

        return VocabularyStatsResponse(
            total_reviewed=stats["total_reviewed"],
            known_words=stats["known_words"],
            unknown_words=stats["unknown_words"],
            percentage_known=stats["percentage_known"],
            level_breakdown=level_breakdown,
        )

    async def get_blocking_words(self, db: Session, user_id: int, text: str, language: str = "de") -> list[str]:
        """Get words that would block user comprehension"""
        # This is a simplified version - in practice, you'd tokenize the text
        # and check each word against user's known vocabulary
        words = text.split()
        blocking_words = []

        for word in words:
            vocab_word = await self.vocabulary_repository.get_by_word(db, word.lower(), language)
            if vocab_word:
                progress = await self.progress_repository.get_user_word_progress(db, user_id, vocab_word.id)
                if not progress or not progress.is_known:
                    blocking_words.append(word)

        return blocking_words
