"""
Debug and logging API routes
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("api.debug")
frontend_logger = logging.getLogger("frontend")
router = APIRouter(prefix="/debug", tags=["debug"])


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
async def receive_frontend_log(log_entry: FrontendLogEntry) -> Dict[str, Any]:
    """Receive and store frontend log entries"""
    try:
        # Log the frontend entry with appropriate level - simplified to avoid issues
        log_level = getattr(logging, log_entry.level.upper(), logging.INFO)

        # Simple log without extra data to avoid any serialization issues
        frontend_logger.log(
            log_level, f"[Frontend][{log_entry.category}] {log_entry.message}"
        )

        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to process frontend log: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/health")
async def debug_health() -> Dict[str, str]:
    """Debug health check endpoint"""
    logger.info("Debug health check called")
    return {
        "status": "healthy",
        "debug_logging": "enabled",
        "timestamp": logging.Formatter().formatTime(
            logging.LogRecord(
                name="debug",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="",
                args=(),
                exc_info=None,
            )
        ),
    }


@router.post("/test-minimal")
async def test_minimal_post() -> Dict[str, str]:
    """Minimal POST endpoint without dependencies"""
    logger.debug("Minimal POST endpoint called - immediate response")
    return {"status": "ok", "message": "Minimal POST endpoint working"}


@router.post("/test-with-data")
async def test_post_with_data(data: Optional[dict] = None) -> Dict[str, Any]:
    """POST endpoint with data"""
    logger.debug(f"POST with data called: {data}")
    return {"status": "ok", "received_data": data}
