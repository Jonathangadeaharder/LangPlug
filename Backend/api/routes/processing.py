"""
Processing API routes - refactored into focused modules

This module aggregates all processing-related routes from specialized modules:
- transcription_routes: Video transcription functionality
- translation_routes: Subtitle translation and selective translation
- filtering_routes: Subtitle filtering and vocabulary processing
- episode_processing_routes: Chunk processing and episode preparation
- pipeline_routes: Full processing pipeline and task progress monitoring
"""

import logging

from fastapi import APIRouter

# Import all focused route modules
from . import (
    episode_processing_routes,
    filtering_routes,
    pipeline_routes,
    transcription_routes,
)

logger = logging.getLogger(__name__)

# Create main processing router
router = APIRouter(tags=["processing"])

# Include all focused routers
router.include_router(transcription_routes.router)
router.include_router(filtering_routes.router)
router.include_router(episode_processing_routes.router)
router.include_router(pipeline_routes.router)


async def _get_user_language_level(user_id: str) -> str | None:
    """
    Get user's current language level from database.

    Args:
        user_id: The user ID to look up

    Returns:
        User's language level or None if not found
    """
    # This is a placeholder implementation
    # In a real implementation, you would query the user profile table
    # to get their current language level preference
    return None


# Export commonly used functions for backward compatibility
from .episode_processing_routes import run_chunk_processing
from .filtering_routes import run_subtitle_filtering
from .transcription_routes import run_transcription

__all__ = [
    "router",
    "run_chunk_processing",
    "run_subtitle_filtering",
    "run_transcription",
]
