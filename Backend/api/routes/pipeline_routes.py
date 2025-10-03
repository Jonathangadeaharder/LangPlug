"""
Pipeline API routes for full processing pipeline and task progress monitoring
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.dependencies import (
    current_active_user,
    get_task_progress_registry,
)
from database.models import User

from ..models.processing import FullPipelineRequest, ProcessingStatus

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pipeline"])


@router.post("/full-pipeline", name="full_pipeline")
async def full_pipeline(
    request: FullPipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Run a full processing pipeline: Transcribe -> Filter -> Translate"""
    try:
        # Import the pipeline function from episode processing routes
        from .episode_processing_routes import run_processing_pipeline

        # Start full pipeline in background
        task_id = f"pipeline_{current_user.id}_{datetime.now().timestamp()}"
        background_tasks.add_task(run_processing_pipeline, request.video_path, task_id, task_progress, current_user.id)

        logger.info(f"Started full processing pipeline task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except Exception as e:
        logger.error(f"Failed to start processing pipeline: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing pipeline failed: {e!s}") from e


@router.get("/progress/{task_id}", name="get_task_progress")
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """
    Monitor progress of a background processing task.

    Polls the status of an active background task (transcription, filtering, translation,
    or full pipeline). Returns current progress percentage, status, and step information.

    **Authentication Required**: Yes

    Args:
        task_id (str): Unique task identifier from task initiation response
        current_user (User): Authenticated user
        task_progress (dict): Task progress tracking registry

    Returns:
        ProcessingStatus: Progress information with:
            - status: "processing", "completed", "error", or "cancelled"
            - progress: Percentage complete (0-100)
            - current_step: Description of current processing step
            - message: Detailed status message
            - vocabulary (optional): Extracted vocabulary (if applicable)
            - subtitle_path (optional): Generated subtitle path (if completed)
            - translation_path (optional): Translation file path (if applicable)

    Raises:
        None (returns completed status for missing tasks)

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/processing/progress/transcribe_123_1234567890.123" \
          -H "Authorization: Bearer <token>"
        ```

        Response (in progress):
        ```json
        {
            "status": "processing",
            "progress": 45.0,
            "current_step": "Transcribing audio segments",
            "message": "Processing segment 45 of 100"
        }
        ```

        Response (completed):
        ```json
        {
            "status": "completed",
            "progress": 100.0,
            "current_step": "Processing complete",
            "message": "Video transcribed successfully",
            "subtitle_path": "Learn German/S01E01.srt"
        }
        ```

    Note:
        Frontend should poll this endpoint periodically (e.g., every 2 seconds)
        until status becomes "completed" or "error". Missing tasks return
        completed status to prevent infinite polling.
    """
    logger.debug(f"[PROGRESS CHECK] Task ID: {task_id}")
    logger.debug(f"[PROGRESS CHECK] Available tasks: {list(task_progress.keys())}")

    if task_id not in task_progress:
        logger.warning(f"[PROGRESS CHECK] Task {task_id} NOT FOUND in registry")
        # Return completed status for missing tasks (likely already completed and cleaned up)
        # This prevents infinite polling in the frontend
        return ProcessingStatus(
            status="completed", progress=100, current_step="Processing complete", message="Task has already completed"
        )

    progress_data = task_progress[task_id]
    # Only log important status changes
    if progress_data.status in {"error", "completed"}:
        logger.info(
            f"[PROGRESS CHECK] Task {task_id} - Status: {progress_data.status}, Progress: {progress_data.progress}%"
        )
    else:
        logger.debug(
            f"[PROGRESS CHECK] Task {task_id} - Status: {progress_data.status}, Progress: {progress_data.progress}%"
        )

    if progress_data.status == "completed":
        logger.info(f"[PROGRESS CHECK] Task {task_id} is COMPLETED!")
        if hasattr(progress_data, "vocabulary"):
            logger.debug(
                f"[PROGRESS CHECK] Vocabulary items: {len(progress_data.vocabulary) if progress_data.vocabulary else 0}"
            )
        if hasattr(progress_data, "subtitle_path"):
            logger.debug(f"[PROGRESS CHECK] Subtitle path: {progress_data.subtitle_path}")
        if hasattr(progress_data, "translation_path"):
            logger.debug(f"[PROGRESS CHECK] Translation path: {getattr(progress_data, 'translation_path', None)}")

    return progress_data
