"""
Repository interfaces for clean architecture implementation

Provides abstract interfaces for repository implementations following
Dependency Inversion Principle. Session is injected via constructor,
not passed to each method.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID", int, str)


class BaseRepositoryInterface(ABC, Generic[T, ID]):
    """Base repository interface defining common CRUD operations.

    Note: Database session is injected via constructor, not passed to methods.
    This aligns with the actual implementation pattern.
    """

    @abstractmethod
    async def create(self, **kwargs: Any) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> T | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0, **filters: Any) -> list[T]:
        """Get multiple entities with pagination and filtering"""
        pass

    @abstractmethod
    async def update_by_id(self, entity_id: ID, **kwargs: Any) -> T | None:
        """Update an entity"""
        pass

    @abstractmethod
    async def delete_by_id(self, entity_id: ID) -> bool:
        """Delete an entity"""
        pass

    @abstractmethod
    async def exists(self, **filters: Any) -> bool:
        """Check if entity exists"""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count entities matching filters"""
        pass


class UserRepositoryInterface(BaseRepositoryInterface[Any, int]):
    """User-specific repository operations"""

    @abstractmethod
    async def find_by_email(self, email: str) -> Any | None:
        """Find user by email"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Any | None:
        """Find user by username"""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        pass

    @abstractmethod
    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user's password"""
        pass

    @abstractmethod
    async def verify_user(self, user_id: int) -> bool:
        """Mark user as verified"""
        pass

    @abstractmethod
    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        pass

    @abstractmethod
    async def activate_user(self, user_id: int) -> bool:
        """Activate a user account"""
        pass


class VocabularyRepositoryInterface(BaseRepositoryInterface[Any, int]):
    """Vocabulary-specific repository operations"""

    @abstractmethod
    async def find_by_lemma(self, lemma: str, language: str = "de") -> Any | None:
        """Find vocabulary word by lemma"""
        pass

    @abstractmethod
    async def find_by_word(self, word: str, language: str) -> Any | None:
        """Find vocabulary word by word and language"""
        pass

    @abstractmethod
    async def get_by_level(self, language: str, level: str, limit: int = 1000, offset: int = 0) -> list[Any]:
        """Get vocabulary words by difficulty level"""
        pass

    @abstractmethod
    async def search_vocabulary(self, search_term: str, language: str = "de", limit: int = 20) -> list[Any]:
        """Search vocabulary words"""
        pass

    @abstractmethod
    async def get_user_progress(self, user_id: int, vocabulary_id: int) -> Any | None:
        """Get user's progress for a specific word"""
        pass

    @abstractmethod
    async def upsert_user_progress(self, user_id: int, vocabulary_id: int, is_known: bool, **kwargs: Any) -> Any:
        """Create or update user vocabulary progress"""
        pass

    @abstractmethod
    async def get_user_vocabulary_stats(self, user_id: int, language: str) -> dict[str, Any]:
        """Get vocabulary statistics for a user"""
        pass

    @abstractmethod
    async def record_unknown_word(self, word: str, lemma: str | None, language: str) -> Any:
        """Record a word not found in vocabulary"""
        pass


class UserVocabularyProgressRepositoryInterface(BaseRepositoryInterface[Any, int]):
    """User vocabulary progress repository operations"""

    @abstractmethod
    async def get_user_progress(self, user_id: int, language: str = "de") -> list[Any]:
        """Get all vocabulary progress for a user"""
        pass

    @abstractmethod
    async def get_user_word_progress(self, user_id: int, vocabulary_id: int) -> Any | None:
        """Get specific word progress for user"""
        pass

    @abstractmethod
    async def mark_word_known(self, user_id: int, vocabulary_id: int, is_known: bool) -> Any:
        """Mark word as known/unknown for user"""
        pass

    @abstractmethod
    async def get_or_create_progress(self, user_id: int, lemma: str, language: str, **kwargs: Any) -> Any:
        """Get existing progress or create new one"""
        pass

    @abstractmethod
    async def bulk_mark_level(self, user_id: int, language: str, level: str, is_known: bool) -> int:
        """Bulk mark all words in a level as known/unknown. Returns count updated."""
        pass


class ProcessingSessionRepositoryInterface(BaseRepositoryInterface[Any, str]):
    """Processing session repository operations"""

    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> Any | None:
        """Get processing session by session ID"""
        pass

    @abstractmethod
    async def update_status(self, session_id: str, status: str, error_message: str | None = None) -> Any | None:
        """Update processing session status"""
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: int, status: str | None = None) -> list[Any]:
        """Get processing sessions for a user"""
        pass

    @abstractmethod
    async def create_session(self, session_id: str, user_id: int | None, content_type: str, **kwargs: Any) -> Any:
        """Create a new processing session"""
        pass

    @abstractmethod
    async def complete_session(
        self, session_id: str, total_words: int, unique_words: int, processing_time: float
    ) -> Any | None:
        """Mark session as completed with stats"""
        pass
