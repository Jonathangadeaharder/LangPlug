"""
ChunkUtilities - File management and user utilities for chunk processing
Extracted from chunk_processor.py for better separation of concerns
"""

from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.processing import ProcessingStatus
from core.config import settings
from core.config.logging_config import get_logger
from core.language_preferences import (
    load_language_preferences,
    resolve_language_runtime_settings,
)
from database.models import User

logger = get_logger(__name__)


class ChunkUtilitiesError(Exception):
    """Exception for chunk utilities errors"""

    pass


class ChunkUtilities:
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
        # Normalize Windows backslashes to forward slashes for WSL compatibility
        normalized_path = video_path.replace("\\", "/")
        if normalized_path.startswith("/"):
            return Path(normalized_path)
        else:
            return settings.get_videos_path() / normalized_path

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
                logger.debug("Session token provided")

            logger.debug("Authenticated user", user_id=user.id)
            return user

        except Exception as e:
            logger.error("Failed to authenticate user", user_id=normalized_id, error=str(e))
            raise ChunkUtilitiesError(f"Authentication failed: {e}") from e

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

        logger.debug("User language preferences", user_id=user.id)
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
                            logger.warning("Could not delete file", error=str(e))

            if cleanup_count > 0:
                logger.debug("Cleaned up old chunk files", count=cleanup_count)

        except Exception as e:
            logger.warning("Chunk cleanup failed", error=str(e))

    def initialize_progress(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        start_time: float,
        end_time: float,
        user_id: int,
    ) -> None:
        """
        Initialize progress tracking for chunk processing

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            video_file: Path to video file
            start_time: Chunk start time
            end_time: Chunk end time
            user_id: User ID for WebSocket routing
        """
        # Create ProcessingStatus instance directly (no WebSocket wrapper for now)
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting chunk processing...",
            message=f"Processing {video_file.name} ({start_time:.1f}s - {end_time:.1f}s)",
        )

        logger.debug("Initialized processing", task_id=task_id)

    def complete_processing(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        vocabulary: list | None = None,
        subtitle_path: str | None = None,
        translation_path: str | None = None,
    ) -> None:
        """
        Mark chunk processing as completed

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            vocabulary: Optional vocabulary results
            subtitle_path: Optional path to subtitle file
            translation_path: Optional path to translation file
        """
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Chunk processing completed"
        task_progress[task_id].message = "Vocabulary extracted and ready for learning"

        if vocabulary:
            task_progress[task_id].vocabulary = vocabulary

        if subtitle_path:
            task_progress[task_id].subtitle_path = subtitle_path
            logger.debug("Set subtitle_path")

        if translation_path:
            task_progress[task_id].translation_path = translation_path
            logger.debug("Set translation_path")

        logger.debug("Completed processing", task_id=task_id)

    def handle_error(self, task_id: str, task_progress: dict[str, Any], error: Exception) -> None:
        """
        Handle error in chunk processing

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            error: Exception that occurred
        """
        # Truncate error message to fit within validation limits (2000 chars)
        error_msg = str(error)[:1900]  # Leave some buffer
        if len(str(error)) > 1900:
            error_msg += "... (truncated)"

        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Processing failed",
            message=f"Error: {error_msg}",
        )

        logger.error("Error in task", task_id=task_id, error=str(error))

    def debug_empty_vocabulary(self, filter_result: dict[str, Any], srt_file_path: str) -> None:
        """
        Debug logging for empty vocabulary results

        Args:
            filter_result: Filtering result dictionary
            srt_file_path: Path to SRT file that was processed
        """
        logger.warning("Empty vocabulary returned from filtering", srt_path=srt_file_path)
