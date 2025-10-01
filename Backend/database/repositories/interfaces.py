"""
Repository interfaces for clean architecture implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")
ID = TypeVar("ID", int, str)


class BaseRepositoryInterface(ABC, Generic[T, ID]):
    """Base repository interface defining common CRUD operations"""

    @abstractmethod
    async def create(self, db: Session, **kwargs) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, db: Session, entity_id: ID) -> T | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_many(
        self, db: Session, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[T]:
        """Get multiple entities with pagination and filtering"""
        pass

    @abstractmethod
    async def update(self, db: Session, entity_id: ID, **kwargs) -> T | None:
        """Update an entity"""
        pass

    @abstractmethod
    async def delete(self, db: Session, entity_id: ID) -> bool:
        """Delete an entity"""
        pass

    @abstractmethod
    async def exists(self, db: Session, entity_id: ID) -> bool:
        """Check if entity exists"""
        pass


class UserRepositoryInterface(BaseRepositoryInterface[Any, int]):
    """User-specific repository operations"""

    @abstractmethod
    async def get_by_email(self, db: Session, email: str) -> Any | None:
        """Get user by email"""
        pass

    @abstractmethod
    async def get_by_username(self, db: Session, username: str) -> Any | None:
        """Get user by username"""
        pass

    @abstractmethod
    async def update_last_login(self, db: Session, user_id: int) -> bool:
        """Update user's last login timestamp"""
        pass


class VocabularyRepositoryInterface(BaseRepositoryInterface[Any, int]):
    """Vocabulary-specific repository operations"""

    @abstractmethod
    async def get_by_lemma(self, db: Session, lemma: str, language: str = "de") -> Any | None:
        """Get vocabulary word by lemma"""
        pass

    @abstractmethod
    async def get_by_difficulty_level(
        self, db: Session, level: str, language: str = "de", skip: int = 0, limit: int = 100
    ) -> list[Any]:
        """Get vocabulary words by difficulty level"""
        pass

    @abstractmethod
    async def search_words(self, db: Session, query: str, language: str = "de", limit: int = 20) -> list[Any]:
        """Search vocabulary words"""
        pass


class UserVocabularyProgressRepositoryInterface(BaseRepositoryInterface[Any, int]):
    """User vocabulary progress repository operations"""

    @abstractmethod
    async def get_user_progress(self, db: Session, user_id: int, language: str = "de") -> list[Any]:
        """Get all vocabulary progress for a user"""
        pass

    @abstractmethod
    async def get_user_word_progress(self, db: Session, user_id: int, vocabulary_id: int) -> Any | None:
        """Get specific word progress for user"""
        pass

    @abstractmethod
    async def mark_word_known(self, db: Session, user_id: int, vocabulary_id: int, is_known: bool) -> Any:
        """Mark word as known/unknown for user"""
        pass


class ProcessingSessionRepositoryInterface(BaseRepositoryInterface[Any, str]):
    """Processing session repository operations"""

    @abstractmethod
    async def get_by_session_id(self, db: Session, session_id: str) -> Any | None:
        """Get processing session by session ID"""
        pass

    @abstractmethod
    async def update_status(
        self, db: Session, session_id: str, status: str, error_message: str | None = None
    ) -> Any | None:
        """Update processing session status"""
        pass

    @abstractmethod
    async def get_user_sessions(self, db: Session, user_id: int, status: str | None = None) -> list[Any]:
        """Get processing sessions for a user"""
        pass
