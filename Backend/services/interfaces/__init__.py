"""
Service interfaces for the LangPlug application.
Provides clean contracts for all service implementations.
"""

# Base interfaces
# Authentication interfaces
from .auth import IAuthService, IPermissionService, ITokenService
from .base import (
    IAsyncService,
    IRepositoryService,
    IService,
    NotFoundError,
    PermissionError,
    ServiceError,
    ValidationError,
)

# Chunk processing interfaces
from .chunk_interface import IChunkProcessingService, IChunkUtilities

# Handler interfaces
from .handler_interface import (
    IChunkHandler,
    IFilteringHandler,
    IPipelineHandler,
    IProcessingHandler,
    ITranscriptionHandler,
    ITranslationHandler,
)

# Processing interfaces
from .processing import (
    IProcessingPipelineService,
    ISubtitleProcessor,
    ITaskProgressService,
    ITranscriptionService,
    ITranslationService,
    IVideoProcessingService,
)

# Transcription interfaces
from .transcription_interface import IChunkTranscriptionService

# Translation interfaces
from .translation_interface import IChunkTranslationService, ISelectiveTranslationService

# Vocabulary interfaces
from .vocabulary import IUserVocabularyService, IVocabularyImportService, IVocabularyPreloadService, IVocabularyService

__all__ = [
    "IAsyncService",
    # Auth
    "IAuthService",
    "IChunkHandler",
    # Chunk Processing
    "IChunkProcessingService",
    "IChunkTranscriptionService",
    "IChunkTranslationService",
    "IChunkUtilities",
    "IFilteringHandler",
    "IPermissionService",
    "IPipelineHandler",
    # Handlers
    "IProcessingHandler",
    "IProcessingPipelineService",
    "IRepositoryService",
    "ISelectiveTranslationService",
    # Base
    "IService",
    "ISubtitleProcessor",
    "ITaskProgressService",
    "ITokenService",
    "ITranscriptionHandler",
    # Processing
    "ITranscriptionService",
    "ITranslationHandler",
    "ITranslationService",
    "IUserVocabularyService",
    "IVideoProcessingService",
    "IVocabularyImportService",
    "IVocabularyPreloadService",
    # Vocabulary
    "IVocabularyService",
    "NotFoundError",
    "PermissionError",
    "ServiceError",
    "ValidationError",
]
