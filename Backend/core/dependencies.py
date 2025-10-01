"""Simplified dependency injection for FastAPI using native Depends system"""

# Re-export commonly used dependencies from focused modules
try:
    from .auth_dependencies import (
        current_active_user,
        get_current_user_ws,
        get_optional_user,
        get_user_from_query_token,
        security,
    )
except ImportError:
    # Fallback for import issues
    pass

try:
    from .service_dependencies import (
        get_chunk_transcription_service,
        get_chunk_translation_service,
        get_chunk_utilities,
        get_subtitle_processor,
        get_transcription_service,
        get_translation_service,
        get_user_subtitle_processor,
        get_vocabulary_service,
    )
except ImportError:
    # Fallback for import issues
    pass

try:
    from .task_dependencies import cleanup_services, get_task_progress_registry, init_services
except ImportError:
    # Fallback for import issues
    cleanup_services = None
    init_services = None

# Export for backward compatibility
__all__ = [
    "cleanup_services",
    "current_active_user",
    "get_chunk_transcription_service",
    "get_chunk_translation_service",
    "get_chunk_utilities",
    "get_current_user_ws",
    "get_optional_user",
    "get_subtitle_processor",
    "get_task_progress_registry",
    "get_transcription_service",
    "get_translation_service",
    "get_user_from_query_token",
    "get_user_subtitle_processor",
    "get_vocabulary_service",
    "init_services",
    "security",
]
