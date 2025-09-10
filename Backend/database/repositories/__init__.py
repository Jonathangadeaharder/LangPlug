"""Repository classes for data access layer."""

from .vocabulary_repository import VocabularyRepository
from .unknown_words_repository import UnknownWordsRepository
from .user_progress_repository import UserProgressRepository
from .word_category_repository import WordCategoryRepository

__all__ = [
    'VocabularyRepository',
    'UnknownWordsRepository',
    'UserProgressRepository',
    'WordCategoryRepository'
]