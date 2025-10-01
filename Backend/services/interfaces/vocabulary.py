"""
Vocabulary service interfaces providing clean contracts for vocabulary operations.
"""

from abc import abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserVocabularyProgress, VocabularyWord

from .base import IAsyncService, IRepositoryService


class IVocabularyService(IRepositoryService[VocabularyWord]):
    """Interface for core vocabulary operations"""

    @abstractmethod
    async def get_word_info(self, word: str, language: str, db: AsyncSession) -> dict[str, Any] | None:
        """Get detailed information about a vocabulary word"""
        pass

    @abstractmethod
    async def search_vocabulary(
        self, search_term: str, language: str = "de", limit: int = 20, db: AsyncSession = None
    ) -> list[dict[str, Any]]:
        """Search vocabulary by term"""
        pass

    @abstractmethod
    async def get_vocabulary_library(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        language: str = "de",
        level: str | None = None,
        known_filter: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Get paginated vocabulary library with optional filters"""
        pass

    @abstractmethod
    async def get_vocabulary_stats(
        self, db: AsyncSession, user_id: int | None = None, language: str = "de"
    ) -> dict[str, Any]:
        """Get vocabulary statistics"""
        pass


class IUserVocabularyService(IAsyncService):
    """Interface for user-specific vocabulary operations"""

    @abstractmethod
    async def mark_word_known(
        self, user_id: int, word: str, language: str, is_known: bool, db: AsyncSession
    ) -> dict[str, Any]:
        """Mark a word as known or unknown for a user"""
        pass

    @abstractmethod
    async def mark_level_known(
        self, db: AsyncSession, user_id: int, language: str, level: str, is_known: bool
    ) -> dict[str, Any]:
        """Mark all words of a level as known or unknown"""
        pass

    @abstractmethod
    async def get_user_progress(self, db: AsyncSession, user_id: int, language: str = "de") -> dict[str, Any]:
        """Get user's vocabulary learning progress"""
        pass

    @abstractmethod
    async def get_user_stats(self, db: AsyncSession, user_id: int, language: str = "de") -> dict[str, Any]:
        """Get detailed user vocabulary statistics"""
        pass

    @abstractmethod
    async def bulk_mark_words(
        self, db: AsyncSession, user_id: int, vocabulary_ids: list[int], is_known: bool
    ) -> list[UserVocabularyProgress]:
        """Bulk mark multiple words as known/unknown"""
        pass


class IVocabularyPreloadService(IAsyncService):
    """Interface for vocabulary preloading and management"""

    @abstractmethod
    async def load_vocabulary_level(
        self, level: str, language: str = "de", force_reload: bool = False
    ) -> dict[str, Any]:
        """Load vocabulary for a specific CEFR level"""
        pass

    @abstractmethod
    async def preload_all_levels(self, language: str = "de", force_reload: bool = False) -> dict[str, Any]:
        """Preload vocabulary for all CEFR levels"""
        pass

    @abstractmethod
    async def verify_vocabulary_integrity(self, language: str = "de") -> dict[str, Any]:
        """Verify vocabulary data integrity"""
        pass

    @abstractmethod
    async def get_preload_status(self, language: str = "de") -> dict[str, Any]:
        """Get status of vocabulary preloading"""
        pass


class IVocabularyImportService(IAsyncService):
    """Interface for importing vocabulary from external sources"""

    @abstractmethod
    async def import_from_csv(
        self, file_path: str, level: str, language: str = "de", target_language: str = "es"
    ) -> dict[str, Any]:
        """Import vocabulary from CSV file"""
        pass

    @abstractmethod
    async def import_from_api(
        self, words: list[str], level: str, language: str = "de", target_language: str = "es"
    ) -> dict[str, Any]:
        """Import vocabulary from external API"""
        pass

    @abstractmethod
    async def validate_import_data(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate vocabulary import data"""
        pass
