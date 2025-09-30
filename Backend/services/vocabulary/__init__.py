"""Vocabulary services package"""

from .vocabulary_query_service import VocabularyQueryService, vocabulary_query_service, get_vocabulary_query_service
from .vocabulary_progress_service import VocabularyProgressService, vocabulary_progress_service, get_vocabulary_progress_service
from .vocabulary_stats_service import VocabularyStatsService, vocabulary_stats_service, get_vocabulary_stats_service
from .vocabulary_service_new import VocabularyService, vocabulary_service, get_vocabulary_service

__all__ = [
    "VocabularyQueryService",
    "vocabulary_query_service",
    "get_vocabulary_query_service",
    "VocabularyProgressService",
    "vocabulary_progress_service",
    "get_vocabulary_progress_service",
    "VocabularyStatsService",
    "vocabulary_stats_service",
    "get_vocabulary_stats_service",
    "VocabularyService",
    "vocabulary_service",
    "get_vocabulary_service",
]
