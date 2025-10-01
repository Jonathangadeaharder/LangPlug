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
        raise HTTPException(status_code=500, detail=f"Processing pipeline failed: {e!s}")


@router.get("/progress/{task_id}", name="get_task_progress")
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Get progress of a background task"""
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
