"""
Domain repository interfaces for the vocabulary domain.
These define the contract for data access from the domain perspective.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .entities import DifficultyLevel, LearningSession, UserVocabularyProgress, VocabularyWord
from .value_objects import Language


class VocabularyDomainRepository(ABC):
    """Domain repository interface for vocabulary operations"""

    @abstractmethod
    async def get_by_id(self, word_id: int) -> VocabularyWord | None:
        """Get vocabulary word by ID"""
        pass

    @abstractmethod
    async def get_by_lemma(self, lemma: str, language: Language) -> VocabularyWord | None:
        """Get vocabulary word by lemma and language"""
        pass

    @abstractmethod
    async def search_words(self, query: str, language: Language, limit: int = 20) -> list[VocabularyWord]:
        """Search vocabulary words"""
        pass

    @abstractmethod
    async def get_by_difficulty_level(
        self, level: DifficultyLevel, language: Language, limit: int = 100, offset: int = 0
    ) -> list[VocabularyWord]:
        """Get words by difficulty level"""
        pass

    @abstractmethod
    async def get_by_frequency_range(self, min_rank: int, max_rank: int, language: Language) -> list[VocabularyWord]:
        """Get words within a frequency rank range"""
        pass

    @abstractmethod
    async def save(self, word: VocabularyWord) -> VocabularyWord:
        """Save vocabulary word"""
        pass

    @abstractmethod
    async def delete(self, word_id: int) -> bool:
        """Delete vocabulary word"""
        pass

    @abstractmethod
    async def get_total_count(self, language: Language) -> int:
        """Get total vocabulary count for language"""
        pass


class UserProgressDomainRepository(ABC):
    """Domain repository interface for user progress operations"""

    @abstractmethod
    async def get_user_progress(self, user_id: int, language: Language) -> list[UserVocabularyProgress]:
        """Get all progress for a user in a language"""
        pass

    @abstractmethod
    async def get_word_progress(self, user_id: int, word_id: int) -> UserVocabularyProgress | None:
        """Get specific word progress for user"""
        pass

    @abstractmethod
    async def get_due_for_review(
        self, user_id: int, language: Language, max_words: int = 20
    ) -> list[UserVocabularyProgress]:
        """Get words due for review"""
        pass

    @abstractmethod
    async def get_recently_learned(
        self, user_id: int, language: Language, days: int = 7
    ) -> list[UserVocabularyProgress]:
        """Get recently learned words"""
        pass

    @abstractmethod
    async def get_mastered_words(self, user_id: int, language: Language) -> list[UserVocabularyProgress]:
        """Get mastered words for user"""
        pass

    @abstractmethod
    async def save(self, progress: UserVocabularyProgress) -> UserVocabularyProgress:
        """Save user progress"""
        pass

    @abstractmethod
    async def save_bulk(self, progress_list: list[UserVocabularyProgress]) -> list[UserVocabularyProgress]:
        """Save multiple progress records efficiently"""
        pass

    @abstractmethod
    async def delete(self, progress_id: int) -> bool:
        """Delete progress record"""
        pass

    @abstractmethod
    async def get_progress_stats(self, user_id: int, language: Language) -> dict[str, Any]:
        """Get progress statistics for user"""
        pass


class LearningSessionDomainRepository(ABC):
    """Domain repository interface for learning session operations"""

    @abstractmethod
    async def create_session(self, session: LearningSession) -> LearningSession:
        """Create a new learning session"""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> LearningSession | None:
        """Get learning session by ID"""
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: int, limit: int = 50, offset: int = 0) -> list[LearningSession]:
        """Get learning sessions for user"""
        pass

    @abstractmethod
    async def get_recent_sessions(self, user_id: int, days: int = 30) -> list[LearningSession]:
        """Get recent learning sessions"""
        pass

    @abstractmethod
    async def update_session(self, session: LearningSession) -> LearningSession:
        """Update learning session"""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete learning session"""
        pass

    @abstractmethod
    async def get_session_analytics(self, user_id: int, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Get session analytics for user in date range"""
        pass


class VocabularyDomainUnitOfWork(ABC):
    """Unit of Work for vocabulary domain operations"""

    vocabulary: VocabularyDomainRepository
    user_progress: UserProgressDomainRepository
    learning_sessions: LearningSessionDomainRepository

    @abstractmethod
    async def __aenter__(self):
        """Enter async context manager"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager"""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes"""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes"""
        pass
