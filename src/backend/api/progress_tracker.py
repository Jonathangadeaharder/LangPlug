"""
Progress Tracker with WebSocket Support

Wraps ProcessingStatus to automatically send WebSocket updates when progress changes.
"""

import asyncio
from typing import Any

from api.models.processing import ProcessingStatus
from api.websocket_manager import manager
from core.config.logging_config import get_logger

logger = get_logger(__name__)

# Global set to hold task references and prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


class ProgressTracker:
    """
    Wrapper for ProcessingStatus that automatically sends WebSocket updates.

    Forwards all attribute access to the wrapped ProcessingStatus instance,
    but sends WebSocket updates whenever progress-related fields are modified.
    """

    def __init__(self, status: ProcessingStatus, task_id: str, user_id: str):
        """
        Initialize progress tracker.

        Args:
            status: ProcessingStatus instance to wrap
            task_id: Task identifier for WebSocket updates
            user_id: User identifier for WebSocket routing
        """
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_task_id", task_id)
        object.__setattr__(self, "_user_id", user_id)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to wrapped ProcessingStatus"""
        return getattr(self._status, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set attribute on wrapped ProcessingStatus and send WebSocket update.

        Args:
            name: Attribute name
            value: New value
        """
        # Get the wrapped objects from __dict__ directly to avoid recursion
        status = object.__getattribute__(self, "_status")
        task_id = object.__getattribute__(self, "_task_id")
        user_id = object.__getattribute__(self, "_user_id")

        # Update the wrapped ProcessingStatus
        setattr(status, name, value)

        # Send WebSocket update for progress-related fields
        if name in ("progress", "status", "current_step", "message"):
            try:
                # Try to get the running event loop and create task
                loop = asyncio.get_running_loop()
                task = loop.create_task(
                    manager.send_user_message(
                        user_id,
                        {
                            "type": "task_progress",
                            "task_id": task_id,
                            "progress": status.progress,
                            "status": str(status.status),
                            "current_step": status.current_step,
                            "message": status.message,
                        },
                    )
                )
                # Store task reference to prevent GC, remove when done
                _background_tasks.add(task)
                task.add_done_callback(_background_tasks.discard)
            except RuntimeError:
                # No running event loop - skip WebSocket update
                # This is expected in synchronous background tasks
                pass
            except Exception as e:
                # Don't fail the task if WebSocket update fails
                logger.debug("Could not send WebSocket update", task_id=task_id, error=str(e))

    def __repr__(self) -> str:
        """String representation"""
        status = object.__getattribute__(self, "_status")
        return f"ProgressTracker({status!r})"

    def model_dump(self, **kwargs) -> dict:
        """Pydantic model_dump for FastAPI serialization"""
        status = object.__getattribute__(self, "_status")
        return status.model_dump(**kwargs)

    def model_dump_json(self, **kwargs) -> str:
        """Pydantic model_dump_json for FastAPI serialization"""
        status = object.__getattribute__(self, "_status")
        return status.model_dump_json(**kwargs)

    @property
    def __dict__(self) -> dict:
        """Dict representation for JSON serialization"""
        status = object.__getattribute__(self, "_status")
        return status.__dict__
