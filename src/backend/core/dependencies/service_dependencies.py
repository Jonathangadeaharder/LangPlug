"""Service dependencies for FastAPI using direct singleton pattern"""

import logging
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.auth_dependencies import current_active_user
from core.database.database import get_async_session as get_db_session
from database.models import User
from services.interfaces import (
    IChunkTranscriptionService,
    IChunkTranslationService,
)

# Type hints for services (avoid circular imports)
if TYPE_CHECKING:
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
    from services.processing.chunk_processor import ChunkProcessingService
    from services.processing.chunk_utilities import ChunkUtilities
    from services.transcriptionservice.interface import ITranscriptionService
    from services.translationservice.interface import ITranslationService
    from services.vocabulary.vocabulary_service import VocabularyService

logger = logging.getLogger(__name__)


# Core service dependencies using direct imports
def get_vocabulary_service(
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> "VocabularyService":
    """Get vocabulary service instance with proper dependency injection"""
    from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
    from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
    from services.vocabulary.vocabulary_service import get_vocabulary_service as _get_vocab_service
    from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

    query_service = get_vocabulary_query_service()
    progress_service = get_vocabulary_progress_service()
    stats_service = get_vocabulary_stats_service()

    return _get_vocab_service(query_service, progress_service, stats_service)


def get_subtitle_processor(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    vocab_service: "VocabularyService" = Depends(get_vocabulary_service),
) -> "DirectSubtitleProcessor":
    """Get subtitle processor instance with injected vocab service"""
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

    return DirectSubtitleProcessor(vocab_service=vocab_service)


def get_user_subtitle_processor(
    current_user: Annotated[User, Depends(current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    vocab_service: "VocabularyService" = Depends(get_vocabulary_service),
) -> "DirectSubtitleProcessor":
    """Get subtitle processor for authenticated user with injected vocab service"""
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

    return DirectSubtitleProcessor(vocab_service=vocab_service)


def get_processing_service(
    db: Annotated[AsyncSession, Depends(get_db_session)] | None = None,
) -> "ChunkProcessingService":
    """Get processing pipeline service instance.
    
    Args:
        db: Optional database session for utilities that need DB access
        
    Returns:
        Configured ChunkProcessingService instance
    """
    from services.processing.chunk_processor import ChunkProcessingService

    return ChunkProcessingService(db_session=db)


def get_transcription_service() -> "ITranscriptionService | None":
    """Get transcription service instance (singleton)"""
    try:
        from core.config.config import settings
        from services.transcriptionservice.factory import get_transcription_service as _get_transcription_service

        logger.info(f"Initializing transcription service: {settings.transcription_service}")
        service = _get_transcription_service(settings.transcription_service)
        logger.info("Transcription service initialized successfully")
        return service
    except ImportError as e:
        if "whisper" in str(e).lower() or "torch" in str(e).lower():
            logger.warning(f"ML dependencies not available for transcription service: {e}")
            logger.info("Install ML dependencies with: pip install -r requirements-ml.txt")
        else:
            logger.error(f"Failed to create transcription service: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create transcription service: {e}")
        return None


def get_translation_service() -> "ITranslationService | None":
    """Get translation service instance"""
    try:
        from core.config.config import settings
        from services.translationservice.factory import get_translation_service as _get_translation_service

        logger.info(f"Initializing translation service: {settings.translation_service}")
        service = _get_translation_service(settings.translation_service)
        logger.info("Translation service initialized successfully")
        return service
    except ImportError as e:
        if "torch" in str(e).lower() or "transformers" in str(e).lower():
            logger.warning(f"ML dependencies not available for translation service: {e}")
            logger.info("Install ML dependencies with: pip install -r requirements-ml.txt")
        else:
            logger.error(f"Failed to create translation service: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create translation service: {e}")
        return None


def get_chunk_transcription_service() -> IChunkTranscriptionService:
    """Get chunk transcription service instance"""
    from services.processing.chunk_transcription_service import ChunkTranscriptionService

    return ChunkTranscriptionService()


def get_chunk_translation_service() -> IChunkTranslationService:
    """Get chunk translation service instance"""
    from services.processing.chunk_translation_service import ChunkTranslationService

    return ChunkTranslationService()


def get_chunk_utilities(db: Annotated[AsyncSession, Depends(get_db_session)]) -> "ChunkUtilities":
    """Get chunk utilities service instance"""
    from services.processing.chunk_utilities import ChunkUtilities

    return ChunkUtilities(db)


__all__ = [
    "get_chunk_transcription_service",
    "get_chunk_translation_service",
    "get_chunk_utilities",
    "get_subtitle_processor",
    "get_transcription_service",
    "get_translation_service",
    "get_user_subtitle_processor",
    "get_vocabulary_service",
]
