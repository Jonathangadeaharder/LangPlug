"""
Debug and logging API routes

Provides endpoints for frontend log aggregation and debugging utilities.
"""

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from core.config.logging_config import get_logger

# Use structlog for this module's logs
logger = get_logger(__name__)

# Standard logging for frontend logs (these get written to file as-is)
frontend_logger = logging.getLogger("frontend")

router = APIRouter(tags=["debug"])


class FrontendLogEntry(BaseModel):
    timestamp: str
    level: str
    category: str
    message: str
    data: Any = None
    error: str | None = None
    stack: str | None = None
    url: str | None = None
    userAgent: str | None = None
    userId: str | None = None


class FrontendLogBatch(BaseModel):
    logs: list[FrontendLogEntry]


def format_log_entry(entry: FrontendLogEntry) -> str:
    """Format a single log entry"""
    log_msg = f"[{entry.category}] {entry.message}"
    if entry.data:
        log_msg += f" | Data: {entry.data}"
    if entry.error:
        log_msg += f" | Error: {entry.error}"
    if entry.url:
        log_msg += f" | URL: {entry.url}"
    if entry.userId:
        log_msg += f" | User: {entry.userId}"
    return log_msg


@router.post("/frontend-logs")
async def log_frontend_entry(payload: FrontendLogEntry | FrontendLogBatch):
    """
    Receive and process log entries from the frontend application.

    Accepts either a single log entry or a batch of log entries from the frontend,
    routing them to the backend logging system for centralized debugging and monitoring.
    Supports standard log levels and includes contextual metadata.

    **Authentication Required**: No

    Args:
        payload (FrontendLogEntry | FrontendLogBatch): Log entry or batch with:
            - timestamp: ISO 8601 timestamp
            - level: Log level ("debug", "info", "warn", "error")
            - category: Log category (e.g., "api", "render", "user-action")
            - message: Log message
            - data (optional): Structured log data
            - error (optional): Error message if applicable
            - stack (optional): Stack trace for errors
            - url (optional): Current page URL
            - userAgent (optional): Browser user agent
            - userId (optional): User identifier

    Returns:
        dict: Acknowledgment with:
            - success: Always true
            - status: "logged"
            - count: Number of log entries processed (for batches)
            - timestamp: Timestamp of first log entry

    Example (single entry):
        ```bash
        curl -X POST "http://localhost:8000/api/debug/frontend-logs" \
          -H "Content-Type: application/json" \
          -d '{
            "timestamp": "2024-10-03T10:30:00.000Z",
            "level": "error",
            "category": "api",
            "message": "Failed to fetch vocabulary",
            "error": "Network request failed",
            "userId": "user-123"
          }'
        ```

    Example (batch):
        ```bash
        curl -X POST "http://localhost:8000/api/debug/frontend-logs" \
          -H "Content-Type: application/json" \
          -d '{
            "logs": [
              {
                "timestamp": "2024-10-03T10:30:00.000Z",
                "level": "info",
                "category": "navigation",
                "message": "User navigated to vocabulary page"
              },
              {
                "timestamp": "2024-10-03T10:30:05.000Z",
                "level": "debug",
                "category": "api",
                "message": "Fetching vocabulary library",
                "data": {"limit": 100, "offset": 0}
              }
            ]
          }'
        ```

    Note:
        Log entries are written to the backend's "frontend" logger and can be
        monitored alongside backend logs for comprehensive debugging.
    """
    # Check if it's a batch or single entry
    if isinstance(payload, FrontendLogBatch):
        # Handle batch
        for entry in payload.logs:
            log_level = getattr(logging, entry.level.upper(), logging.INFO)
            log_msg = format_log_entry(entry)
            frontend_logger.log(log_level, log_msg)

        return {
            "success": True,
            "status": "logged",
            "count": len(payload.logs),
            "timestamp": payload.logs[0].timestamp if payload.logs else None,
        }
    else:
        # Handle single entry (backward compatibility)
        log_level = getattr(logging, payload.level.upper(), logging.INFO)
        log_msg = format_log_entry(payload)
        frontend_logger.log(log_level, log_msg)

        return {"success": True, "status": "logged", "timestamp": payload.timestamp}


@router.get("/health")
async def debug_health():
    """
    Debug health check endpoint
    """
    return {"status": "healthy", "service": "langplug-backend", "debug_mode": True}
