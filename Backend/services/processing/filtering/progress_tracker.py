"""
Progress tracking service for filtering operations
"""

import time
from typing import Any

from api.models.processing import ProcessingStatus


class ProgressTrackerService:
    """Manages progress tracking for filtering tasks"""

    def initialize(self, task_id: str, task_progress: dict[str, Any]) -> None:
        """Initialize progress tracking for a new task"""
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting filtering...",
            message="Loading subtitle file",
            started_at=int(time.time()),
        )

    def update_progress(
        self, task_progress: dict[str, Any], task_id: str, progress: float, current_step: str, message: str
    ) -> None:
        """Update progress tracking with current status"""
        task_progress[task_id].progress = progress
        task_progress[task_id].current_step = current_step
        task_progress[task_id].message = message

    def mark_complete(self, task_progress: dict[str, Any], task_id: str, result: Any) -> None:
        """Mark task as completed"""
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].message = "Filtering completed successfully"
        task_progress[task_id].result = result
        task_progress[task_id].completed_at = int(time.time())

    def mark_failed(self, task_progress: dict[str, Any], task_id: str, error: Exception) -> None:
        """Mark task as failed"""
        task_progress[task_id].status = "failed"
        task_progress[task_id].error = str(error)
        task_progress[task_id].message = f"Filtering failed: {error!s}"


# Global instance
progress_tracker_service = ProgressTrackerService()


def get_progress_tracker_service() -> ProgressTrackerService:
    """Get the global progress tracker service instance"""
    return progress_tracker_service
