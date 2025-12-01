"""
Episode Processing API routes for chunk processing and episode preparation
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from api.websocket_manager import manager as websocket_manager
from core.config import settings
from core.config.logging_config import get_logger
from core.dependencies import (
    current_active_user,
    get_task_progress_registry,
)
from database.models import User
from services.progress import ProgressTracker, WebSocketBroadcaster

from ..models.processing import (
    ChunkProcessingRequest,
    ProcessingStatus,
)

logger = get_logger(__name__)
router = APIRouter(tags=["episode-processing"])


async def run_chunk_processing(
    video_path: str,
    start_time: float,
    end_time: float,
    task_id: str,
    task_progress: dict[str, Any],
    user_id: int,
    session_token: str | None = None,
    is_reprocessing: bool = False,
) -> None:
    """
    Process a specific chunk of video for vocabulary learning.

    Includes real-time WebSocket progress broadcasting for connected clients.
    Falls back gracefully to polling if WebSocket is not connected.
    """
    from core.database import get_async_session
    from services.processing.chunk_processor import (
        ChunkProcessingService,
    )

    # Setup progress tracker with WebSocket broadcasting
    progress_tracker = ProgressTracker(task_id, task_progress)

    # Enable WebSocket real-time updates if manager has connections for this user
    user_id_str = str(user_id)
    if websocket_manager.get_user_connection_count(user_id_str) > 0:
        broadcaster = WebSocketBroadcaster(websocket_manager)
        progress_tracker.set_broadcaster(broadcaster, user_id_str)
        logger.debug("WebSocket broadcasting enabled", user_id=user_id_str, task_id=task_id)
    else:
        logger.debug("No WebSocket connections, using polling", user_id=user_id_str)

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
                is_reprocessing=is_reprocessing,
            )
            break  # Only use the first (and only) session

    except Exception as e:
        logger.error("Chunk processing failed", task_id=task_id, error=str(e), exc_info=True)
        # Truncate error message to fit within validation limits (2000 chars)
        error_msg = str(e)[:1900]  # Leave some buffer
        if len(str(e)) > 1900:
            error_msg += "... (truncated)"

        # Update progress registry for polling
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Chunk processing failed",
            message=f"Error: {error_msg}",
        )

        # Also broadcast error via WebSocket if available
        await progress_tracker.fail(error_msg, "Chunk processing failed")


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

        logger.info("Processing chunk", video_path=str(full_path))

        # Validate chunk timing first
        if request.start_time < 0 or request.end_time <= request.start_time:
            raise HTTPException(status_code=400, detail="Invalid chunk timing")

        if not full_path.exists():
            logger.warning("Video file not found", path=str(full_path))
            raise HTTPException(status_code=404, detail="Video file not found")

        # Start chunk processing in background
        task_id = (
            f"chunk_{current_user.id}_{int(request.start_time)}_{int(request.end_time)}_{datetime.now().timestamp()}"
        )

        # Initialize task in registry BEFORE returning to prevent race condition
        # where frontend polls before background task starts
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Initializing",
            message="Starting chunk processing...",
        )

        background_tasks.add_task(
            run_chunk_processing,
            str(full_path),
            request.start_time,
            request.end_time,
            task_id,
            task_progress,
            current_user.id,
            None,  # session_token
            request.is_reprocessing,
        )

        logger.info("Chunk processing started", task_id=task_id)
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chunk processing failed", error=str(e), exc_info=True)
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
