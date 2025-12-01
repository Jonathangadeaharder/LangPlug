"""
Progress Tracking Infrastructure

Provides a unified interface for tracking and broadcasting progress updates
across background tasks. Supports both polling and WebSocket real-time updates.

Design Principles:
    - Single Responsibility: Track progress, delegate broadcasting
    - Dependency Injection: Accept broadcaster implementations
    - Async-first: Non-blocking progress updates
    - Graceful degradation: Works without WebSocket

Usage Example:
    ```python
    tracker = ProgressTracker(task_id, task_progress_dict)
    tracker.set_broadcaster(websocket_manager, user_id)

    async for segment in transcription_generator:
        await tracker.update(
            progress=calculate_progress(segment),
            step="Transcribing audio...",
            message=f"Processing segment {segment.index}"
        )

    await tracker.complete(result_data)
    ```
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProgressUpdate:
    """Immutable progress update data"""

    progress: float  # 0-100
    step: str
    message: str
    status: str = "processing"
    metadata: dict[str, Any] = field(default_factory=dict)


class ProgressBroadcaster(Protocol):
    """Protocol for progress broadcasting implementations"""

    async def broadcast_progress(self, user_id: str, task_id: str, update: ProgressUpdate) -> None:
        """Broadcast progress update to connected clients"""
        ...


class WebSocketBroadcaster:
    """WebSocket-based progress broadcaster"""

    def __init__(self, websocket_manager):
        self.manager = websocket_manager

    async def broadcast_progress(self, user_id: str, task_id: str, update: ProgressUpdate) -> None:
        """Send progress via WebSocket"""
        try:
            message = {
                "type": "task_progress",
                "task_id": task_id,
                "progress": update.progress,
                "status": update.status,
                "current_step": update.step,
                "message": update.message,
                "timestamp": time.time(),
                **update.metadata,
            }
            await self.manager.send_user_message(user_id, message)
        except Exception as e:
            logger.warning("Failed to broadcast progress via WebSocket", error=str(e))


class ProgressTracker:
    """
    Unified progress tracking with optional real-time broadcasting.

    Manages progress state in the shared registry (for polling) and
    optionally broadcasts updates via WebSocket for real-time UX.

    Attributes:
        task_id: Unique identifier for the task
        task_progress: Shared progress registry dictionary
        broadcaster: Optional WebSocket broadcaster
        user_id: User ID for WebSocket targeting

    Example:
        ```python
        tracker = ProgressTracker("task_123", progress_dict)

        # Enable WebSocket broadcasting
        tracker.set_broadcaster(WebSocketBroadcaster(ws_manager), "user_456")

        # Update progress (writes to registry + broadcasts)
        await tracker.update(progress=50, step="Processing", message="Halfway done")

        # Mark complete
        await tracker.complete({"result": "success"})
        ```
    """

    def __init__(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        min_update_interval: float = 0.5,  # Throttle updates to avoid flooding
    ):
        self.task_id = task_id
        self.task_progress = task_progress
        self.broadcaster: ProgressBroadcaster | None = None
        self.user_id: str | None = None
        self.min_update_interval = min_update_interval
        self._last_update_time: float = 0
        self._last_progress: float = 0

    def set_broadcaster(self, broadcaster: ProgressBroadcaster, user_id: str) -> None:
        """Enable real-time broadcasting via WebSocket"""
        self.broadcaster = broadcaster
        self.user_id = user_id

    async def update(
        self, progress: float, step: str, message: str, status: str = "processing", force: bool = False, **metadata
    ) -> None:
        """
        Update progress in registry and optionally broadcast.

        Throttles updates to avoid flooding WebSocket connections.
        Use force=True to bypass throttling for important updates.
        """
        current_time = time.time()

        # Throttle updates unless forced or significant progress change
        progress_delta = abs(progress - self._last_progress)
        time_delta = current_time - self._last_update_time

        should_update = (
            force or time_delta >= self.min_update_interval or progress_delta >= 5.0  # Always update on 5% jumps
        )

        if not should_update:
            return

        self._last_update_time = current_time
        self._last_progress = progress

        # Update registry (for polling fallback)
        if self.task_id in self.task_progress:
            entry = self.task_progress[self.task_id]
            entry.progress = progress
            entry.current_step = step
            entry.message = message
            entry.status = status
            for key, value in metadata.items():
                setattr(entry, key, value)

        # Broadcast via WebSocket if configured
        if self.broadcaster and self.user_id:
            update = ProgressUpdate(progress=progress, step=step, message=message, status=status, metadata=metadata)
            # Fire and forget - don't block on broadcast
            asyncio.create_task(self.broadcaster.broadcast_progress(self.user_id, self.task_id, update))

    async def complete(
        self, result: dict[str, Any] | None = None, message: str = "Processing completed successfully"
    ) -> None:
        """Mark task as complete with optional result data"""
        await self.update(
            progress=100.0,
            step="Complete",
            message=message,
            status="completed",
            force=True,
            completed_at=int(time.time()),
            **(result or {}),
        )

    async def fail(self, error: str, message: str | None = None) -> None:
        """Mark task as failed with error details"""
        await self.update(
            progress=self._last_progress,
            step="Failed",
            message=message or f"Processing failed: {error}",
            status="failed",
            force=True,
            error=error,
        )


class TranscriptionProgressCallback:
    """
    Progress callback for transcription services.

    Provides a callable interface that transcription services can use
    to report progress without knowing about the tracking infrastructure.

    Usage:
        ```python
        callback = TranscriptionProgressCallback(tracker, progress_range=(5, 35))

        # In transcription service:
        await callback(0.5, "Transcribing segment 10/20")  # Reports 20% (5 + 0.5*30)
        ```
    """

    def __init__(
        self,
        tracker: ProgressTracker,
        progress_range: tuple[float, float] = (0, 100),
        step_name: str = "Transcribing audio...",
    ):
        self.tracker = tracker
        self.start_progress, self.end_progress = progress_range
        self.range_size = self.end_progress - self.start_progress
        self.step_name = step_name

    async def __call__(self, fraction: float, message: str, force: bool = False) -> None:
        """
        Report progress as a fraction (0-1) within the configured range.

        Args:
            fraction: Progress within this phase (0.0 to 1.0)
            message: Human-readable status message
            force: Bypass update throttling
        """
        progress = self.start_progress + (fraction * self.range_size)
        await self.tracker.update(progress=progress, step=self.step_name, message=message, force=force)


class TranslationProgressCallback(TranscriptionProgressCallback):
    """Alias for translation progress with appropriate defaults"""

    def __init__(
        self,
        tracker: ProgressTracker,
        progress_range: tuple[float, float] = (65, 95),
        step_name: str = "Translating segments...",
    ):
        super().__init__(tracker, progress_range, step_name)
