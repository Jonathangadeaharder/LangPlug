"""
Logging API routes for receiving and managing frontend logs
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["logs"])


class LogEntry(BaseModel):
    timestamp: str
    level: str
    component: str
    message: str
    data: str = None


class LogBatch(BaseModel):
    entries: list[LogEntry]
    client_id: str = "frontend"


@router.post("/frontend", name="logs_receive_frontend")
async def receive_frontend_logs(log_batch: LogBatch):
    """Receive and save frontend logs to file"""
    try:
        # Create logs directory
        logs_path = settings.get_logs_path()
        logs_path.mkdir(exist_ok=True)

        # Create frontend log filename with date
        today = datetime.now().strftime("%Y-%m-%d")
        frontend_log_file = logs_path / f"langplug-frontend-{today}.log"

        # Format and append logs
        log_lines = []
        for entry in log_batch.entries:
            parts = [entry.timestamp, f"[{entry.level}]", f"{entry.component}:", entry.message]
            if entry.data:
                parts.append(f"| {entry.data}")
            log_lines.append(" ".join(parts))

        # Append to log file
        with open(frontend_log_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(log_lines) + '\n')

        logger.info(f"📝 Saved {len(log_batch.entries)} frontend log entries to {frontend_log_file}")

        return {
            "success": True,
            "entries_saved": len(log_batch.entries),
            "log_file": str(frontend_log_file)
        }

    except Exception as e:
        logger.error(f"Failed to save frontend logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save logs: {e!s}")


@router.get("/list", name="logs_list_files")
async def list_log_files():
    """List available log files"""
    try:
        logs_path = settings.get_logs_path()
        if not logs_path.exists():
            return {"log_files": []}

        log_files = []
        for log_file in logs_path.glob("*.log*"):
            stat = log_file.stat()
            log_files.append({
                "name": log_file.name,
                "path": str(log_file),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        # Sort by modification time, newest first
        log_files.sort(key=lambda x: x["modified"], reverse=True)

        return {"log_files": log_files}

    except Exception as e:
        logger.error(f"Failed to list log files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list logs: {e!s}")


@router.get("/download/{filename}", name="logs_download_file")
async def download_log_file(filename: str):
    """Download a specific log file"""
    try:
        logs_path = settings.get_logs_path()
        log_file = logs_path / filename

        if not log_file.exists() or not log_file.is_file():
            raise HTTPException(status_code=404, detail="Log file not found")

        # Read and return file content
        with open(log_file, encoding='utf-8') as f:
            content = f.read()

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download log file {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download log: {e!s}")
