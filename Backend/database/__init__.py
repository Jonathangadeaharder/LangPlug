"""Database package for A1Decider vocabulary management."""

from .unified_database_manager import UnifiedDatabaseManager as DatabaseManager
from .repositories import (
    VocabularyRepository,
    UnknownWordsRepository,
    UserProgressRepository,
    WordCategoryRepository
)

__all__ = [
    'DatabaseManager',
    'VocabularyRepository',
    'UnknownWordsRepository', 
    'UserProgressRepository',
    'WordCategoryRepository'
]