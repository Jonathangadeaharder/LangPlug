"""
Parallel Transcription API Routes

10x faster transcription using parallel chunk processing.
Based on research from fast-audio-video-transcribe.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.dependencies import current_active_user, get_transcription_service
from database.models import User
from services.parallel_transcription.job_tracker import get_job_tracker, JobStatus
from services.parallel_transcription.parallel_transcriber import (
    ParallelTranscriber,
    ParallelTranscriptionError
)
from utils.media_validator import is_valid_video_file

logger = logging.getLogger(__name__)
router = APIRouter(tags=["parallel-transcription"])


class ParallelTranscribeRequest(BaseModel):
    """Request for parallel transcription"""
    video_path: str
    language: str = "de"
    max_workers: int = 4


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    progress: float
    message: str
    started_at: float
    updated_at: float
    completed_at: float | None = None
    error: str | None = None
    result: dict | None = None


async def _run_parallel_transcription(
    job_id: str,
    video_path: Path,
    language: str,
    max_workers: int,
    transcription_service: any
):
    """
    Background task for parallel transcription.

    Args:
        job_id: Unique job identifier
        video_path: Path to video file
        language: Target language
        max_workers: Number of parallel workers
        transcription_service: Whisper transcription service
    """
    job_tracker = get_job_tracker()

    try:
        logger.info(f"Starting parallel transcription: {job_id}")

        # Update status to processing
        job_tracker.update_progress(
            job_id,
            0,
            "Initializing parallel transcription",
            JobStatus.PROCESSING
        )

        # Create parallel transcriber
        transcriber = ParallelTranscriber(
            transcription_service=transcription_service,
            max_workers=max_workers
        )

        # Progress callback
        def update_progress(progress: float):
            message = f"Processing: {progress:.0f}%"
            if progress < 10:
                message = "Creating chunks..."
            elif progress < 25:
                message = "Extracting audio chunks..."
            elif progress < 90:
                message = f"Transcribing chunks ({progress:.0f}%)..."
            elif progress < 100:
                message = "Assembling results..."
            else:
                message = "Complete!"

            job_tracker.update_progress(job_id, progress, message)

        # Run parallel transcription
        result = await transcriber.transcribe_parallel(
            video_path=video_path,
            language=language,
            progress_callback=update_progress
        )

        # Mark job as completed
        job_tracker.complete_job(
            job_id,
            result={
                'srt_path': result['srt_path'],
                'chunks_processed': result['chunks_processed'],
                'video_path': str(video_path),
                'language': language,
            },
            message=f"Transcribed {result['chunks_processed']} chunks successfully"
        )

        logger.info(f"Parallel transcription completed: {job_id}")

    except ParallelTranscriptionError as e:
        logger.error(f"Parallel transcription failed: {job_id} - {e}")
        job_tracker.fail_job(job_id, str(e), "Parallel transcription failed")

    except Exception as e:
        logger.error(f"Unexpected error in parallel transcription: {job_id} - {e}", exc_info=True)
        job_tracker.fail_job(job_id, str(e), "Internal transcription error")


@router.post("/transcribe-parallel", name="transcribe_parallel")
async def transcribe_parallel(
    request: ParallelTranscribeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    transcription_service=Depends(get_transcription_service),
):
    """
    Transcribe video using parallel processing for 10x speed improvement.

    Processes audio in parallel chunks for faster transcription:
    - Splits audio into 30s chunks at silence points
    - Transcribes chunks concurrently (default: 4 workers)
    - Reassembles segments with correct timestamps
    - Generates SRT file

    **Performance**: ~1 minute for 1-hour video (vs 10 minutes serial)

    **Authentication Required**: Yes

    Args:
        request: Transcription request with:
            - video_path: Path to video file
            - language: Target language (default: "de")
            - max_workers: Parallel workers (default: 4)
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        transcription_service: Whisper transcription service

    Returns:
        dict with:
            - job_id: Unique job identifier
            - status: "queued"
            - poll_url: URL to check job status

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/processing/transcribe-parallel" \\
          -H "Authorization: Bearer <token>" \\
          -H "Content-Type: application/json" \\
          -d '{
            "video_path": "Learn German/S01E01.mp4",
            "language": "de",
            "max_workers": 4
          }'
        ```

        Response:
        ```json
        {
            "job_id": "transcribe_parallel_abc123",
            "status": "queued",
            "poll_url": "/api/processing/transcribe-parallel/status/transcribe_parallel_abc123"
        }
        ```

    Note:
        Use /api/processing/transcribe-parallel/status/{job_id} to poll for progress.
        Job status updates every ~0.5 seconds during processing.
    """
    try:
        # Validate transcription service
        if transcription_service is None:
            raise HTTPException(
                status_code=422,
                detail="Transcription service not available"
            )

        # Validate video path
        videos_path = settings.get_videos_path()
        normalized_path = request.video_path.replace("\\", "/")
        full_path = Path(normalized_path) if normalized_path.startswith("/") else videos_path / normalized_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        if not is_valid_video_file(str(full_path)):
            raise HTTPException(status_code=422, detail="Unsupported video format")

        # Validate max_workers
        if request.max_workers < 1 or request.max_workers > 16:
            raise HTTPException(
                status_code=422,
                detail="max_workers must be between 1 and 16"
            )

        # Create job ID
        job_id = f"transcribe_parallel_{current_user.id}_{uuid.uuid4().hex[:8]}"

        # Create job in tracker
        job_tracker = get_job_tracker()
        job_tracker.create_job(str(full_path), job_id)

        # Start background task
        background_tasks.add_task(
            _run_parallel_transcription,
            job_id,
            full_path,
            request.language,
            request.max_workers,
            transcription_service
        )

        logger.info(f"Started parallel transcription job: {job_id}")

        return {
            "job_id": job_id,
            "status": "queued",
            "poll_url": f"/api/processing/transcribe-parallel/status/{job_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start parallel transcription: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start transcription: {str(e)}"
        ) from e


@router.get("/transcribe-parallel/status/{job_id}", name="get_parallel_transcription_status")
async def get_parallel_transcription_status(
    job_id: str,
    current_user: User = Depends(current_active_user),
) -> JobStatusResponse:
    """
    Get parallel transcription job status.

    Poll this endpoint to track transcription progress.
    Job data expires after 1 hour of completion.

    **Authentication Required**: Yes

    Args:
        job_id: Job identifier from /transcribe-parallel
        current_user: Authenticated user

    Returns:
        JobStatusResponse with:
            - job_id: Job identifier
            - status: "queued" | "processing" | "completed" | "failed"
            - progress: 0-100
            - message: Status message
            - result: Result data (if completed)
            - error: Error message (if failed)

    Raises:
        HTTPException: 404 if job not found

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/processing/transcribe-parallel/status/transcribe_parallel_abc123" \\
          -H "Authorization: Bearer <token>"
        ```

        Response (processing):
        ```json
        {
            "job_id": "transcribe_parallel_abc123",
            "status": "processing",
            "progress": 45.0,
            "message": "Transcribing chunks (45%)...",
            "started_at": 1234567890.123,
            "updated_at": 1234567895.456
        }
        ```

        Response (completed):
        ```json
        {
            "job_id": "transcribe_parallel_abc123",
            "status": "completed",
            "progress": 100.0,
            "message": "Transcribed 4 chunks successfully",
            "result": {
                "srt_path": "/videos/video.srt",
                "chunks_processed": 4,
                "video_path": "/videos/video.mp4",
                "language": "de"
            },
            "completed_at": 1234567900.789
        }
        ```
    """
    job_tracker = get_job_tracker()
    job = job_tracker.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=job.progress,
        message=job.message,
        started_at=job.started_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        error=job.error,
        result=job.result
    )


@router.get("/transcribe-parallel/active", name="list_active_parallel_jobs")
async def list_active_parallel_jobs(
    current_user: User = Depends(current_active_user),
):
    """
    List all active parallel transcription jobs for current user.

    Returns jobs that are queued or processing (not completed/failed).

    **Authentication Required**: Yes

    Returns:
        dict with:
            - jobs: List of active jobs with status
            - count: Number of active jobs

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/processing/transcribe-parallel/active" \\
          -H "Authorization: Bearer <token>"
        ```

        Response:
        ```json
        {
            "jobs": [
                {
                    "job_id": "transcribe_parallel_abc123",
                    "status": "processing",
                    "progress": 45.0,
                    "message": "Transcribing chunks..."
                }
            ],
            "count": 1
        }
        ```
    """
    job_tracker = get_job_tracker()
    all_active = job_tracker.list_active_jobs()

    # Filter by current user (check if job_id contains user ID)
    user_jobs = {
        job_id: job
        for job_id, job in all_active.items()
        if f"_{current_user.id}_" in job_id
    }

    jobs_list = [
        {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "message": job.message,
            "started_at": job.started_at,
            "updated_at": job.updated_at,
        }
        for job in user_jobs.values()
    ]

    return {
        "jobs": jobs_list,
        "count": len(jobs_list)
    }
