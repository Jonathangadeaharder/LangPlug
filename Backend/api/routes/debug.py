"""
Debug and logging API routes
"""

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("api.debug")
frontend_logger = logging.getLogger("frontend")
router = APIRouter(tags=["debug"])


class FrontendLogEntry(BaseModel):
    timestamp: str
    level: str
    category: str
    message: str
    data: Any = None
    error: str = None
    stack: str = None
    url: str = None
    userAgent: str = None
    userId: str = None


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
    Log entries from the frontend application.
    Accepts either a single log entry or a batch of log entries.
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
            "timestamp": payload.logs[0].timestamp if payload.logs else None
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
