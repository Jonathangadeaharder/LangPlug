"""Service dependencies for FastAPI using direct singleton pattern"""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.interfaces import *

from .auth_dependencies import current_active_user
from .database import get_async_session as get_db_session

logger = logging.getLogger(__name__)


# Core service dependencies using direct imports
def get_vocabulary_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> IVocabularyService:
    """Get vocabulary service singleton instance"""
    from services.vocabulary_service import vocabulary_service

    return vocabulary_service


def get_subtitle_processor(db: Annotated[AsyncSession, Depends(get_db_session)]) -> ISubtitleProcessor:
    """Get subtitle processor instance"""
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

    return DirectSubtitleProcessor()


def get_user_subtitle_processor(
    current_user: Annotated[User, Depends(current_active_user)], db: Annotated[AsyncSession, Depends(get_db_session)]
) -> ISubtitleProcessor:
    """Get subtitle processor for authenticated user"""
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

    return DirectSubtitleProcessor()


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> IAuthService:
    """Get authentication service instance"""
    from services.authservice.auth_service import AuthService

    return AuthService(db)


def get_processing_service() -> IProcessingPipelineService:
    """Get processing pipeline service instance"""
    from services.processing.chunk_processor import ChunkProcessingService

    return ChunkProcessingService()


def get_transcription_service() -> ITranscriptionService | None:
    """Get transcription service instance (singleton)"""
    try:
        from services.transcriptionservice.factory import get_transcription_service as _get_transcription_service

        from .config import settings

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


@lru_cache
def get_translation_service() -> ITranslationService | None:
    """Get translation service instance (singleton)"""
    try:
        from services.translationservice.factory import get_translation_service as _get_translation_service

        from .config import settings

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


def get_chunk_utilities(db: Annotated[AsyncSession, Depends(get_db_session)]) -> IChunkUtilities:
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
