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
    TranscribeRequest,
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
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Chunk processing failed",
            message=f"Error: {e!s}",
        )


@router.post("/chunk", name="process_chunk")
async def process_chunk(
    request: ChunkProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Process a specific chunk of video for vocabulary learning"""
    try:
        full_path = (
            Path(request.video_path)
            if request.video_path.startswith("/")
            else settings.get_videos_path() / request.video_path
        )
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
        raise HTTPException(status_code=500, detail=f"Chunk processing failed: {e!s}")


