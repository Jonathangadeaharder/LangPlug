"""Repository for vocabulary-related database operations using domain entities"""

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UnknownWord, UserVocabularyProgress
from database.models import VocabularyWord as VocabularyWordModel
from domains.vocabulary.entities import DifficultyLevel, VocabularyWord, WordType

from .base_repository import BaseRepository
from .interfaces import VocabularyRepositoryInterface


class VocabularyRepository(BaseRepository[VocabularyWordModel], VocabularyRepositoryInterface):
    """Repository for vocabulary database operations using domain entities"""

    def __init__(self, session: AsyncSession):
        super().__init__(VocabularyWordModel, session)

    async def find_by_word(self, word: str, language: str) -> VocabularyWord | None:
        """Find vocabulary word by word and language"""
        stmt = select(VocabularyWordModel).where(
            and_(VocabularyWordModel.word == word, VocabularyWordModel.language == language)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_domain_entity(model)
        return None

    async def find_by_lemma(self, lemma: str, language: str) -> VocabularyWord | None:
        """Find vocabulary word by lemma and language"""
        stmt = select(VocabularyWordModel).where(
            and_(VocabularyWordModel.lemma == lemma, VocabularyWordModel.language == language)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return self._to_domain_entity(model)
        return None

    async def search_vocabulary(self, search_term: str, language: str, limit: int = 20) -> list[VocabularyWord]:
        """Search vocabulary by word or lemma"""
        search_pattern = f"%{search_term}%"
        stmt = (
            select(VocabularyWordModel)
            .where(
                and_(
                    VocabularyWordModel.language == language,
                    or_(
                        VocabularyWordModel.word.ilike(search_pattern), VocabularyWordModel.lemma.ilike(search_pattern)
                    ),
                )
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_entity(model) for model in models]

    async def get_by_level(self, language: str, level: str, limit: int = 1000, offset: int = 0) -> list[VocabularyWord]:
        """Get vocabulary words by language and level"""
        stmt = (
            select(VocabularyWordModel)
            .where(and_(VocabularyWordModel.language == language, VocabularyWordModel.level == level))
            .order_by(VocabularyWordModel.frequency.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_entity(model) for model in models]

    async def get_user_progress(self, user_id: int, vocabulary_id: int) -> UserVocabularyProgress | None:
        """Get user's progress for a specific word"""
        stmt = select(UserVocabularyProgress).where(
            and_(UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.vocabulary_id == vocabulary_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_user_progress(
        self, user_id: int, vocabulary_id: int, is_known: bool, **kwargs
    ) -> UserVocabularyProgress:
        """Create or update user vocabulary progress"""
        progress = await self.get_user_progress(user_id, vocabulary_id)

        if progress:
            for key, value in kwargs.items():
                setattr(progress, key, value)
            progress.is_known = is_known
        else:
            progress = UserVocabularyProgress(user_id=user_id, vocabulary_id=vocabulary_id, is_known=is_known, **kwargs)
            self.session.add(progress)

        await self.session.commit()
        await self.session.refresh(progress)
        return progress

    async def get_user_vocabulary_stats(self, user_id: int, language: str) -> dict[str, Any]:
        """Get vocabulary statistics for a user"""
        # Total words in language
        total_stmt = select(func.count()).select_from(VocabularyWord).where(VocabularyWord.language == language)
        total_result = await self.session.execute(total_stmt)
        total_count = total_result.scalar() or 0

        # Known words
        known_stmt = (
            select(func.count())
            .select_from(UserVocabularyProgress)
            .join(VocabularyWord)
            .where(
                and_(
                    UserVocabularyProgress.user_id == user_id,
                    UserVocabularyProgress.is_known,
                    VocabularyWord.language == language,
                )
            )
        )
        known_result = await self.session.execute(known_stmt)
        known_count = known_result.scalar() or 0

        # Level breakdown
        level_stmt = (
            select(
                VocabularyWord.level,
                func.count().label("total"),
                func.count().filter(UserVocabularyProgress.is_known).label("known"),
            )
            .select_from(VocabularyWord)
            .outerjoin(
                UserVocabularyProgress,
                and_(
                    UserVocabularyProgress.vocabulary_id == VocabularyWord.id, UserVocabularyProgress.user_id == user_id
                ),
            )
            .where(VocabularyWord.language == language)
            .group_by(VocabularyWord.level)
        )
        level_result = await self.session.execute(level_stmt)

        levels = {}
        for row in level_result:
            levels[row.level] = {
                "total": row.total,
                "known": row.known or 0,
                "percentage": round((row.known or 0) / row.total * 100, 1) if row.total else 0,
            }

        return {
            "total_words": total_count,
            "known_words": known_count,
            "unknown_words": total_count - known_count,
            "percentage": round(known_count / total_count * 100, 1) if total_count else 0,
            "levels": levels,
        }

    async def record_unknown_word(self, word: str, lemma: str | None, language: str) -> UnknownWord:
        """Record a word not found in vocabulary"""
        stmt = select(UnknownWord).where(and_(UnknownWord.word == word, UnknownWord.language == language))
        result = await self.session.execute(stmt)
        unknown = result.scalar_one_or_none()

        if unknown:
            unknown.frequency_count += 1
        else:
            unknown = UnknownWord(word=word, lemma=lemma, language=language, frequency_count=1)
            self.session.add(unknown)

        await self.session.commit()
        await self.session.refresh(unknown)
        return unknown

    def _to_domain_entity(self, model: VocabularyWordModel) -> VocabularyWord:
        """Convert database model to domain entity"""
        try:
            difficulty_level = DifficultyLevel(model.level or "A1")
        except ValueError:
            difficulty_level = DifficultyLevel.A1

        try:
            word_type = WordType(getattr(model, "word_type", None) or "unknown")
        except ValueError:
            word_type = WordType.UNKNOWN

        return VocabularyWord(
            id=model.id,
            word=model.word,
            lemma=model.lemma,
            language=model.language,
            difficulty_level=difficulty_level,
            word_type=word_type,
            definition=model.definition,
            example_sentence=model.example_sentence,
            pronunciation=getattr(model, "pronunciation", None),
            etymology=getattr(model, "etymology", None),
            frequency_rank=getattr(model, "frequency", None),
            translations=getattr(model, "translations", None),
            related_words=getattr(model, "related_words", None),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_database_model(self, entity: VocabularyWord) -> VocabularyWordModel:
        """Convert domain entity to database model"""
        return VocabularyWordModel(
            id=entity.id,
            word=entity.word,
            lemma=entity.lemma,
            language=entity.language,
            level=entity.difficulty_level.value,
            definition=entity.definition,
            example_sentence=entity.example_sentence,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
