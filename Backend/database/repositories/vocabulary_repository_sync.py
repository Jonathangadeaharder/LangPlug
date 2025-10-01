"""
Repository for vocabulary-related database operations - Synchronous version
"""

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from database.models import VocabularyWord
from database.repositories.base_repository_sync import BaseSyncRepository
from database.repositories.interfaces import VocabularyRepositoryInterface


class VocabularyRepositorySync(BaseSyncRepository[VocabularyWord, int], VocabularyRepositoryInterface):
    """Repository for vocabulary operations"""

    def __init__(self):
        super().__init__(VocabularyWord)

    async def get_by_lemma(self, db: Session, lemma: str, language: str = "de") -> VocabularyWord | None:
        """Get vocabulary word by lemma"""
        return (
            db.query(VocabularyWord)
            .filter(and_(VocabularyWord.lemma == lemma, VocabularyWord.language == language))
            .first()
        )

    async def get_by_word(self, db: Session, word: str, language: str = "de") -> VocabularyWord | None:
        """Get vocabulary word by exact word match"""
        return (
            db.query(VocabularyWord)
            .filter(and_(VocabularyWord.word == word, VocabularyWord.language == language))
            .first()
        )

    async def get_by_difficulty_level(
        self, db: Session, level: str, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[VocabularyWord]:
        """Get vocabulary words by difficulty level"""
        return (
            db.query(VocabularyWord)
            .filter(and_(VocabularyWord.difficulty_level == level, VocabularyWord.language == language))
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def search_words(
        self, db: Session, query: str, language: str = "de", limit: int = 20
    ) -> list[VocabularyWord]:
        """Search vocabulary words by word or lemma"""
        search_pattern = f"%{query.lower()}%"
        return (
            db.query(VocabularyWord)
            .filter(
                and_(
                    VocabularyWord.language == language,
                    or_(
                        func.lower(VocabularyWord.word).like(search_pattern),
                        func.lower(VocabularyWord.lemma).like(search_pattern),
                    ),
                )
            )
            .limit(limit)
            .all()
        )

    async def get_random_words(
        self, db: Session, language: str = "de", difficulty_levels: list[str] | None = None, limit: int = 10
    ) -> list[VocabularyWord]:
        """Get random vocabulary words"""
        query = db.query(VocabularyWord).filter(VocabularyWord.language == language)

        if difficulty_levels:
            query = query.filter(VocabularyWord.difficulty_level.in_(difficulty_levels))

        return query.order_by(func.random()).limit(limit).all()

    async def count_by_difficulty(self, db: Session, language: str = "de") -> dict[str, int]:
        """Count vocabulary words by difficulty level"""
        results = (
            db.query(VocabularyWord.difficulty_level, func.count(VocabularyWord.id).label("count"))
            .filter(VocabularyWord.language == language)
            .group_by(VocabularyWord.difficulty_level)
            .all()
        )
        return {row.difficulty_level: row.count for row in results}

    async def get_words_by_frequency_range(
        self, db: Session, min_frequency: int, max_frequency: int, language: str = "de", limit: int = 100
    ) -> list[VocabularyWord]:
        """Get words within a frequency rank range"""
        return (
            db.query(VocabularyWord)
            .filter(
                and_(
                    VocabularyWord.language == language,
                    VocabularyWord.frequency_rank >= min_frequency,
                    VocabularyWord.frequency_rank <= max_frequency,
                )
            )
            .order_by(VocabularyWord.frequency_rank)
            .limit(limit)
            .all()
        )
