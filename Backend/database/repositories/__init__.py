"""Database repositories for clean data access"""

# Legacy async repositories
from .base_repository_sync import BaseSyncRepository

# New sync repositories and interfaces
from .interfaces import (
    BaseRepositoryInterface,
    ProcessingSessionRepositoryInterface,
    UserRepositoryInterface,
    UserVocabularyProgressRepositoryInterface,
    VocabularyRepositoryInterface,
)
from .processing_repository import ProcessingRepository
from .processing_session_repository import ProcessingSessionRepository
from .user_repository import UserRepository
from .user_repository_sync import UserRepositorySync
from .user_vocabulary_progress_repository import UserVocabularyProgressRepository
from .vocabulary_repository import VocabularyRepository
from .vocabulary_repository_sync import VocabularyRepositorySync

__all__ = [
    # Interfaces
    "BaseRepositoryInterface",
    # Sync implementations
    "BaseSyncRepository",
    "ProcessingRepository",
    "ProcessingSessionRepository",
    "ProcessingSessionRepositoryInterface",
    "UserRepository",
    "UserRepositoryInterface",
    "UserRepositorySync",
    "UserVocabularyProgressRepository",
    "UserVocabularyProgressRepositoryInterface",
    # Legacy
    "VocabularyRepository",
    "VocabularyRepositoryInterface",
    "VocabularyRepositorySync",
]
