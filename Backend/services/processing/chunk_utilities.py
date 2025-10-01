"""
ChunkUtilities - File management and user utilities for chunk processing
Extracted from chunk_processor.py for better separation of concerns
"""

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.processing import ProcessingStatus
from core.config import settings
from core.language_preferences import (
    load_language_preferences,
    resolve_language_runtime_settings,
)
from database.models import User
from services.interfaces.chunk_interface import IChunkUtilities

logger = logging.getLogger(__name__)


class ChunkUtilitiesError(Exception):
    """Exception for chunk utilities errors"""

    pass


class ChunkUtilities(IChunkUtilities):
    """
    Utility functions for chunk processing including file management and user operations
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    def resolve_video_path(self, video_path: str) -> Path:
        """
        Resolve video path to absolute path

        Args:
            video_path: Video path (absolute or relative)

        Returns:
            Absolute Path to video file
        """
        if video_path.startswith("/"):
            return Path(video_path)
        else:
            return settings.get_videos_path() / video_path

    async def get_authenticated_user(self, user_identifier: Any, session_token: str | None) -> User:
        """
        Get authenticated user from database

        Args:
            user_identifier: User ID (int, str, or UUID)
            session_token: Optional session token for additional validation

        Returns:
            User object from database

        Raises:
            ChunkUtilitiesError: If user not found or authentication fails
        """
        normalized_id = self._normalize_user_identifier(user_identifier)

        try:
            query = select(User).where(User.id == normalized_id)
            result = await self.db_session.execute(query)
            user = result.scalar_one_or_none()

            if user is None:
                raise ChunkUtilitiesError(f"User not found with ID: {normalized_id}")

            # Session token validation can be added here if needed
            if session_token:
                # For now, just log that a session token was provided
                # In the future, this could validate the token against active sessions
                logger.debug(f"Session token provided: {session_token[:8]}...")

            logger.debug(f"[CHUNK DEBUG] Authenticated user: {user.id} ({user.username})")
            return user

        except Exception as e:
            logger.error(f"Failed to authenticate user {normalized_id}: {e}")
            raise ChunkUtilitiesError(f"Authentication failed: {e}")

    @staticmethod
    def _normalize_user_identifier(user_identifier: Any) -> Any:
        """
        Normalize user identifier to consistent format

        Args:
            user_identifier: User ID in various formats

        Returns:
            Normalized user identifier
        """
        if isinstance(user_identifier, str):
            try:
                # Try to parse as UUID first
                return str(UUID(user_identifier))
            except ValueError:
                # If not UUID, try to parse as int
                try:
                    return int(user_identifier)
                except ValueError:
                    # Return as string if neither works
                    return user_identifier
        return user_identifier

    def load_user_language_preferences(self, user: User) -> dict[str, Any]:
        """
        Load user's language preferences

        Args:
            user: User object

        Returns:
            Dictionary containing language preferences
        """
        native, target = load_language_preferences(str(user.id))
        resolved_preferences = resolve_language_runtime_settings(native, target)

        logger.debug(f"[CHUNK DEBUG] User {user.id} language preferences: {resolved_preferences}")
        return resolved_preferences

    def cleanup_old_chunk_files(self, video_file: Path, start_time: float, end_time: float) -> None:
        """
        Clean up old chunk-related files to prevent accumulation

        Args:
            video_file: Path to the video file
            start_time: Chunk start time
            end_time: Chunk end time
        """
        try:
            # Define patterns for chunk files to clean up
            chunk_patterns = [
                f"*chunk_{int(start_time)}_{int(end_time)}*",
                f"*{video_file.stem}_chunk*",
                "*temp_chunk*",
            ]

            cleanup_count = 0
            for pattern in chunk_patterns:
                for old_file in video_file.parent.glob(pattern):
                    if old_file.is_file() and old_file != video_file:
                        try:
                            old_file.unlink()
                            cleanup_count += 1
                        except OSError as e:
                            logger.warning(f"Could not delete {old_file}: {e}")

            if cleanup_count > 0:
                logger.info(f"[CHUNK DEBUG] Cleaned up {cleanup_count} old chunk files")

        except Exception as e:
            logger.warning(f"Chunk cleanup failed: {e}")

    def initialize_progress(
        self, task_id: str, task_progress: dict[str, Any], video_file: Path, start_time: float, end_time: float
    ) -> None:
        """
        Initialize progress tracking for chunk processing

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            video_file: Path to video file
            start_time: Chunk start time
            end_time: Chunk end time
        """
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting chunk processing...",
            message=f"Processing {video_file.name} ({start_time:.1f}s - {end_time:.1f}s)",
        )

        logger.info(f"[CHUNK DEBUG] Initialized processing for task {task_id}")

    def complete_processing(self, task_id: str, task_progress: dict[str, Any], vocabulary: list | None = None) -> None:
        """
        Mark chunk processing as completed

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            vocabulary: Optional vocabulary results
        """
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Chunk processing completed"
        task_progress[task_id].message = "Vocabulary extracted and ready for learning"

        if vocabulary:
            task_progress[task_id].vocabulary = vocabulary

        logger.info(f"[CHUNK DEBUG] Completed processing for task {task_id}")

    def handle_error(self, task_id: str, task_progress: dict[str, Any], error: Exception) -> None:
        """
        Handle error in chunk processing

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            error: Exception that occurred
        """
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Processing failed",
            message=f"Error: {error!s}",
        )

        logger.error(f"[CHUNK DEBUG] Error in task {task_id}: {error}")

    def debug_empty_vocabulary(self, filter_result: dict[str, Any], srt_file_path: str) -> None:
        """
        Debug logging for empty vocabulary results

        Args:
            filter_result: Filtering result dictionary
            srt_file_path: Path to SRT file that was processed
        """
        logger.warning("[CHUNK DEBUG] Empty vocabulary returned from filtering")
        logger.warning(f"[CHUNK DEBUG] SRT file: {srt_file_path}")
        logger.warning(f"[CHUNK DEBUG] Filter result keys: {list(filter_result.keys()) if filter_result else 'None'}")

        if filter_result:
            for key, value in filter_result.items():
                if isinstance(value, list):
                    logger.warning(f"[CHUNK DEBUG] {key}: {len(value)} items")
                else:
                    logger.warning(f"[CHUNK DEBUG] {key}: {value}")
        else:
            logger.warning("[CHUNK DEBUG] Filter result is None or empty")
