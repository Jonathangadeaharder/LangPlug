"""
Job Tracking System for Background Transcription

Tracks transcription job status with optional Redis backend.
Falls back to in-memory storage if Redis unavailable.

Features:
- Job status tracking (queued, processing, completed, failed)
- Progress updates (0-100%)
- Result storage
- TTL support (auto-cleanup after 1 hour)
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionJob:
    """Transcription job data"""
    job_id: str
    status: JobStatus
    progress: float  # 0-100
    message: str
    video_path: str
    started_at: float
    updated_at: float
    completed_at: float | None = None
    error: str | None = None
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TranscriptionJob':
        """Create from dictionary"""
        data['status'] = JobStatus(data['status'])
        return cls(**data)


class JobTracker:
    """
    Track transcription jobs with optional Redis backend.

    If Redis is available, jobs are stored in Redis with TTL.
    Otherwise, falls back to in-memory dictionary.

    Example:
        ```python
        tracker = JobTracker(redis_client=redis_client)

        # Create job
        job_id = tracker.create_job("video.mp4")

        # Update progress
        tracker.update_progress(job_id, 50, "Processing chunk 5/10")

        # Mark complete
        tracker.complete_job(job_id, {"srt_path": "video.srt"})

        # Get status
        job = tracker.get_job(job_id)
        print(f"Status: {job.status}, Progress: {job.progress}%")
        ```
    """

    JOB_TTL = 3600  # 1 hour

    def __init__(self, redis_client: Any = None):
        """
        Initialize job tracker.

        Args:
            redis_client: Optional Redis client (redis.Redis instance)
        """
        self.redis = redis_client
        self._memory_store: dict[str, TranscriptionJob] = {}

        if self.redis:
            try:
                self.redis.ping()
                logger.info("JobTracker using Redis backend")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory storage: {e}")
                self.redis = None
        else:
            logger.info("JobTracker using in-memory storage")

    def create_job(self, video_path: str, job_id: str) -> str:
        """
        Create a new transcription job.

        Args:
            video_path: Path to video file
            job_id: Unique job identifier

        Returns:
            Job ID
        """
        now = time.time()

        job = TranscriptionJob(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress=0.0,
            message="Job queued",
            video_path=video_path,
            started_at=now,
            updated_at=now
        )

        self._save_job(job)
        logger.info(f"Created job: {job_id}")

        return job_id

    def update_progress(
        self,
        job_id: str,
        progress: float,
        message: str,
        status: JobStatus = JobStatus.PROCESSING
    ) -> None:
        """
        Update job progress.

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Status message
            status: Job status (default: PROCESSING)
        """
        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Job not found for progress update: {job_id}")
            return

        job.status = status
        job.progress = min(100.0, max(0.0, progress))
        job.message = message
        job.updated_at = time.time()

        self._save_job(job)
        logger.debug(f"Job {job_id}: {progress:.1f}% - {message}")

    def complete_job(
        self,
        job_id: str,
        result: dict[str, Any],
        message: str = "Transcription completed"
    ) -> None:
        """
        Mark job as completed.

        Args:
            job_id: Job identifier
            result: Job result data
            message: Completion message
        """
        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Job not found for completion: {job_id}")
            return

        job.status = JobStatus.COMPLETED
        job.progress = 100.0
        job.message = message
        job.result = result
        job.completed_at = time.time()
        job.updated_at = time.time()

        self._save_job(job)
        logger.info(f"Job completed: {job_id}")

    def fail_job(
        self,
        job_id: str,
        error: str,
        message: str = "Transcription failed"
    ) -> None:
        """
        Mark job as failed.

        Args:
            job_id: Job identifier
            error: Error message
            message: Failure message
        """
        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Job not found for failure: {job_id}")
            return

        job.status = JobStatus.FAILED
        job.message = message
        job.error = error
        job.completed_at = time.time()
        job.updated_at = time.time()

        self._save_job(job)
        logger.error(f"Job failed: {job_id} - {error}")

    def get_job(self, job_id: str) -> TranscriptionJob | None:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            TranscriptionJob or None if not found
        """
        if self.redis:
            try:
                key = self._make_key(job_id)
                data = self.redis.get(key)

                if data:
                    job_dict = json.loads(data)
                    return TranscriptionJob.from_dict(job_dict)

            except Exception as e:
                logger.error(f"Failed to get job from Redis: {e}")

        # Fallback to memory
        return self._memory_store.get(job_id)

    def delete_job(self, job_id: str) -> None:
        """
        Delete job from storage.

        Args:
            job_id: Job identifier
        """
        if self.redis:
            try:
                key = self._make_key(job_id)
                self.redis.delete(key)
            except Exception as e:
                logger.error(f"Failed to delete job from Redis: {e}")

        if job_id in self._memory_store:
            del self._memory_store[job_id]

        logger.info(f"Deleted job: {job_id}")

    def _save_job(self, job: TranscriptionJob) -> None:
        """Save job to storage backend"""
        if self.redis:
            try:
                key = self._make_key(job.job_id)
                data = json.dumps(job.to_dict())
                self.redis.setex(key, self.JOB_TTL, data)
            except Exception as e:
                logger.error(f"Failed to save job to Redis: {e}")

        # Always save to memory as backup
        self._memory_store[job.job_id] = job

    def _make_key(self, job_id: str) -> str:
        """Make Redis key for job"""
        return f"langplug:transcription:job:{job_id}"

    def list_active_jobs(self) -> dict[str, TranscriptionJob]:
        """
        List all active (non-completed, non-failed) jobs.

        Returns:
            Dictionary of job_id -> TranscriptionJob
        """
        active_jobs = {}

        if self.redis:
            try:
                pattern = self._make_key("*")
                keys = self.redis.keys(pattern)

                for key in keys:
                    data = self.redis.get(key)
                    if data:
                        job_dict = json.loads(data)
                        job = TranscriptionJob.from_dict(job_dict)

                        if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                            active_jobs[job.job_id] = job

            except Exception as e:
                logger.error(f"Failed to list jobs from Redis: {e}")

        # Also check memory store
        for job_id, job in self._memory_store.items():
            if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING] and job_id not in active_jobs:
                active_jobs[job_id] = job

        return active_jobs


# Global instance (will be initialized with Redis client if available)
_job_tracker: JobTracker | None = None


def get_job_tracker(redis_client: Any = None) -> JobTracker:
    """
    Get global job tracker instance.

    Args:
        redis_client: Optional Redis client (only used on first call)

    Returns:
        JobTracker instance
    """
    global _job_tracker

    if _job_tracker is None:
        _job_tracker = JobTracker(redis_client=redis_client)

    return _job_tracker
