"""
Episode Processing API routes for chunk processing and episode preparation
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.config import settings
from core.dependencies import (
    current_active_user,
    get_task_progress_registry,
)
from database.models import User

from ..models.processing import (
    ChunkProcessingRequest,
    ProcessingStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["episode-processing"])


async def run_chunk_processing(
    video_path: str,
    start_time: float,
    end_time: float,
    task_id: str,
    task_progress: dict[str, Any],
    user_id: int,
    session_token: str | None = None,
) -> None:
    """Process a specific chunk of video for vocabulary learning"""
    from core.database import get_async_session
    from services.processing.chunk_processor import ChunkProcessingService

    try:
        # Get database session and create service instance
        async for db_session in get_async_session():
            chunk_processor = ChunkProcessingService(db_session)
            await chunk_processor.process_chunk(
                video_path=video_path,
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
                task_id=task_id,
                task_progress=task_progress,
                session_token=session_token,
            )
            break  # Only use the first (and only) session

    except Exception as e:
        logger.error(f"Chunk processing failed for task {task_id}: {e}", exc_info=True)
        # Truncate error message to fit within validation limits (2000 chars)
        error_msg = str(e)[:1900]  # Leave some buffer
        if len(str(e)) > 1900:
            error_msg += "... (truncated)"

        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Chunk processing failed",
            message=f"Error: {error_msg}",
        )


@router.post("/chunk", name="process_chunk")
async def process_chunk(
    request: ChunkProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """
    Process a specific time-based chunk of video for vocabulary extraction and learning.

    Extracts vocabulary from a defined time segment of a video, performing transcription,
    translation, and vocabulary analysis on the specified chunk. Useful for focused
    learning on specific video segments.

    **Authentication Required**: Yes

    Args:
        request (ChunkProcessingRequest): Chunk specification with:
            - video_path (str): Relative or absolute path to video file
            - start_time (float): Chunk start time in seconds (>= 0)
            - end_time (float): Chunk end time in seconds (> start_time)
        background_tasks (BackgroundTasks): FastAPI background task manager
        current_user (User): Authenticated user
        task_progress (dict): Task progress tracking registry

    Returns:
        dict: Task initiation response with:
            - task_id: Unique task identifier for progress tracking
            - status: "started"

    Raises:
        HTTPException: 400 if chunk timing is invalid
        HTTPException: 404 if video file not found
        HTTPException: 500 if task initialization fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/processing/chunk" \
          -H "Authorization: Bearer <token>" \
          -H "Content-Type: application/json" \
          -d '{
            "video_path": "Learn German/S01E01.mp4",
            "start_time": 120.0,
            "end_time": 180.0
          }'
        ```

        Response:
        ```json
        {
            "task_id": "chunk_123_120_180_1234567890.123",
            "status": "started"
        }
        ```

    Note:
        Use the returned task_id with /api/processing/progress/{task_id} to monitor
        chunk processing. Completed processing returns extracted vocabulary and
        generates chunk-specific subtitle segments.
    """
    try:
        # Normalize Windows backslashes to forward slashes for WSL compatibility
        normalized_path = request.video_path.replace("\\", "/")
        full_path = (
            Path(normalized_path) if normalized_path.startswith("/") else settings.get_videos_path() / normalized_path
        )

        logger.info(f"Processing chunk for video: {full_path}")

        # Validate chunk timing first
        if request.start_time < 0 or request.end_time <= request.start_time:
            raise HTTPException(status_code=400, detail="Invalid chunk timing")

        if not full_path.exists():
            logger.error(f"Video file not found: {full_path}")
            raise HTTPException(status_code=404, detail="Video file not found")

        # Start chunk processing in background
        task_id = (
            f"chunk_{current_user.id}_{int(request.start_time)}_{int(request.end_time)}_{datetime.now().timestamp()}"
        )
        background_tasks.add_task(
            run_chunk_processing,
            str(full_path),
            request.start_time,
            request.end_time,
            task_id,
            task_progress,
            current_user.id,
        )

        logger.info(f"Started chunk processing task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start chunk processing: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chunk processing failed: {e!s}") from e


async def run_processing_pipeline(
    video_path: str,
    task_id: str,
    task_progress: dict[str, Any],
    user_id: int,
) -> None:
    """
    Full processing pipeline stub (deprecated - use individual endpoints).

    This function was removed during refactoring. Use the following endpoints instead:
    1. POST /api/process/transcribe - Transcribe video
    2. POST /api/process/filter-subtitles - Filter vocabulary
    3. POST /api/process/apply-selective-translations - Translate filtered words

    TODO: Remove this stub and update pipeline_routes.py to use the correct endpoints.
    """
    raise NotImplementedError(
        "Full pipeline processing has been deprecated. "
        "Use individual endpoints: /transcribe, /filter-subtitles, /apply-selective-translations"
    )
