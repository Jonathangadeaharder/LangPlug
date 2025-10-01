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


@router.post("/frontend-logs")
async def log_frontend_entry(entry: FrontendLogEntry):
    """
    Log an entry from the frontend application
    """
    log_level = getattr(logging, entry.level.upper(), logging.INFO)

    # Format the log message
    log_msg = f"[{entry.category}] {entry.message}"
    if entry.data:
        log_msg += f" | Data: {entry.data}"
    if entry.error:
        log_msg += f" | Error: {entry.error}"
    if entry.url:
        log_msg += f" | URL: {entry.url}"
    if entry.userId:
        log_msg += f" | User: {entry.userId}"

    # Log with the appropriate level
    frontend_logger.log(log_level, log_msg)

    return {"success": True, "status": "logged", "timestamp": entry.timestamp}


@router.get("/health")
async def debug_health():
    """
    Debug health check endpoint
    """
    return {"status": "healthy", "service": "langplug-backend", "debug_mode": True}
