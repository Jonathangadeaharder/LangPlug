"""
Service interfaces for the LangPlug application.
Provides clean contracts for all service implementations.
"""

# Base interfaces
from .base import (
    IAsyncService,
    IRepositoryService,
    IService,
    NotFoundError,
    PermissionError,
    ServiceError,
    ValidationError,
)

# Handler interfaces
from .handler_interface import (
    IChunkHandler,
    IFilteringHandler,
    IPipelineHandler,
    IProcessingHandler,
    ITranscriptionHandler,
    ITranslationHandler,
)

# Transcription interfaces
from .transcription_interface import IChunkTranscriptionService

# Translation interfaces
from .translation_interface import IChunkTranslationService, ISelectiveTranslationService

__all__ = [
    # Base interfaces
    "IAsyncService",
    "IRepositoryService",
    "IService",
    "NotFoundError",
    "PermissionError",
    "ServiceError",
    "ValidationError",
    # Handler interfaces
    "IChunkHandler",
    "IFilteringHandler",
    "IPipelineHandler",
    "IProcessingHandler",
    "ITranscriptionHandler",
    "ITranslationHandler",
    # Transcription interfaces
    "IChunkTranscriptionService",
    # Translation interfaces
    "IChunkTranslationService",
    "ISelectiveTranslationService",
]
