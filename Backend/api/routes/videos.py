"""
Video management API routes
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.video import VideoInfo
from api.models.vocabulary import VocabularyWord
from core.config import settings
from core.database import get_async_session
from core.dependencies import current_active_user, get_task_progress_registry, get_user_from_query_token
from core.file_security import FileSecurityValidator
from database.models import User
from services.videoservice.video_service import VideoService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["videos"])


def get_video_service(db_session: AsyncSession = Depends(get_async_session)) -> VideoService:
    """Get video service instance"""
    return VideoService(db_session, None)


@router.get("", response_model=list[VideoInfo], name="get_videos")
async def get_available_videos(
    current_user: User = Depends(current_active_user), video_service: VideoService = Depends(get_video_service)
):
    """
    Retrieve list of all available videos and series for the current user.

    Scans the configured videos directory and returns metadata for all accessible
    video files, including subtitle availability and episode information.

    **Authentication Required**: Yes

    Args:
        current_user (User): Authenticated user
        video_service (VideoService): Video service dependency

    Returns:
        list[VideoInfo]: List of video metadata objects containing:
            - series: Series/show name
            - season: Season number
            - episode: Episode number
            - title: Episode title
            - path: Relative file path
            - has_subtitles: Whether subtitles exist
            - duration: Video duration in seconds

    Raises:
        HTTPException: 500 if directory scanning fails

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/videos" \
          -H "Authorization: Bearer <token>"
        ```

        Response:
        ```json
        [
            {
                "series": "Learn German",
                "season": "1",
                "episode": "01",
                "title": "Introduction",
                "path": "Learn German/S01E01.mp4",
                "has_subtitles": true,
                "duration": 1200
            }
        ]
        ```
    """
    return video_service.get_available_videos()


@router.get("/subtitles/{subtitle_path:path}", name="get_subtitles")
async def get_subtitles(
    subtitle_path: str,
    current_user: User = Depends(current_active_user),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Serve subtitle files (SRT format) for video playback.

    Returns subtitle file content as plain text with UTF-8 encoding.
    Validates file existence and applies security checks to prevent path traversal.

    **Authentication Required**: Yes

    Args:
        subtitle_path (str): Relative path to subtitle file
        current_user (User): Authenticated user
        video_service (VideoService): Video service dependency

    Returns:
        FileResponse: SRT file content with UTF-8 encoding

    Raises:
        HTTPException: 404 if subtitle file not found or invalid
        HTTPException: 500 if file serving fails

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/videos/subtitles/Learn German/S01E01.srt" \
          -H "Authorization: Bearer <token>"
        ```

        Response: (plain text SRT content)
        ```
        1
        00:00:00,000 --> 00:00:05,000
        Hallo und willkommen!

        2
        00:00:05,500 --> 00:00:10,000
        Heute lernen wir Deutsch.
        ```
    """
    try:
        logger.info(f"Serving subtitles: {subtitle_path}")

        subtitle_file = video_service.get_subtitle_file_path(subtitle_path)

        # Verify file exists and is readable
        if not subtitle_file.exists():
            logger.warning(f"Subtitle file not found: {subtitle_file}")
            raise HTTPException(status_code=404, detail="Subtitle file not found")

        if not subtitle_file.is_file():
            logger.warning(f"Subtitle path is not a file: {subtitle_file}")
            raise HTTPException(status_code=404, detail="Invalid subtitle file")

        logger.info(f"Successfully serving subtitle file: {subtitle_file}")
        return FileResponse(
            path=str(subtitle_file), media_type="text/plain", headers={"Content-Type": "text/plain; charset=utf-8"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving subtitles {subtitle_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving subtitles: {e!s}") from e


@router.get(
    "/{series}/{episode}",
    name="stream_video",
    responses={
        200: {"description": "Full video content"},
        206: {"description": "Partial video content (range request)"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Video file not accessible"},
        500: {"description": "Error streaming video"},
    },
)
async def stream_video(
    series: str,
    episode: str,
    current_user: User = Depends(get_user_from_query_token),
    video_service: VideoService = Depends(get_video_service),
):
    """Stream video file - Requires authentication"""
    try:
        video_file = video_service.get_video_file_path(series, episode)

        if not video_file.exists():
            logger.error(f"Video file exists check failed: {video_file}")
            raise HTTPException(status_code=404, detail="Video file not accessible")

        response = FileResponse(
            video_file,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Range",
            },
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stream_video: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error streaming video: {e!s}") from e


@router.post("/subtitle/upload", name="upload_subtitle")
async def upload_subtitle(
    video_path: str, subtitle_file: UploadFile = File(...), current_user: User = Depends(current_active_user)
):
    """
    Upload subtitle file for a video - Requires authentication
    Uses FileSecurityValidator for secure file handling
    """
    try:
        # Validate file security using FileSecurityValidator
        allowed_extensions = {".srt", ".vtt", ".sub"}
        try:
            safe_path = await FileSecurityValidator.validate_file_upload(subtitle_file, allowed_extensions)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        content = await subtitle_file.read()

        videos_path = settings.get_videos_path()
        try:
            video_file_path = str(videos_path / video_path)
            FileSecurityValidator.validate_file_path(video_file_path)
            video_file = videos_path / video_path
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid video path: {e}") from e

        if not video_file.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        subtitle_path = video_file.with_suffix(".srt")

        with open(subtitle_path, "wb") as buffer:
            buffer.write(content)

        logger.info(f"[SECURITY] Uploaded subtitle: {subtitle_path}")

        return {
            "success": True,
            "message": f"Subtitle uploaded for {video_path}",
            "subtitle_path": str(subtitle_path.relative_to(videos_path)),
        }

    except HTTPException:
        raise
    except (OSError, PermissionError) as e:
        logger.error(f"Error uploading subtitle: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading subtitle: {e!s}") from e


@router.post("/scan", name="scan_videos")
async def scan_videos(
    current_user: User = Depends(current_active_user), video_service: VideoService = Depends(get_video_service)
):
    """Scan videos directory for new videos - Requires authentication"""
    return video_service.scan_videos_directory()


@router.get("/user", response_model=list[dict[str, Any]], name="get_user_videos")
async def get_user_videos(
    current_user: User = Depends(current_active_user), video_service: VideoService = Depends(get_video_service)
):
    """Get videos for the current user (alias for get_available_videos)"""
    return video_service.get_available_videos()


@router.get("/{video_id}/vocabulary", response_model=list[VocabularyWord], name="get_video_vocabulary")
async def get_video_vocabulary(video_id: str, current_user: User = Depends(current_active_user)):
    """Get vocabulary words extracted from a video"""
    try:
        videos_path = settings.get_videos_path()
        video_path = videos_path / video_id

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")

        srt_path = video_path.with_suffix(".srt")
        if not srt_path.exists():
            raise HTTPException(status_code=404, detail="Subtitles not found for this video")

        from api.routes.vocabulary import extract_blocking_words_for_segment

        vocabulary_words = await extract_blocking_words_for_segment(str(srt_path), 0, 999999, current_user.id)

        logger.info(f"Extracted {len(vocabulary_words)} vocabulary words for video {video_id}")
        return vocabulary_words

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting vocabulary for video {video_id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error extracting vocabulary: {e!s}") from e


class ProcessingStatus(BaseModel):
    status: str
    progress: float
    current_step: str
    message: str = ""
    subtitle_path: str = ""


@router.get("/{video_id}/status", response_model=ProcessingStatus, name="get_video_status")
async def get_video_status(
    video_id: str,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Get processing status for a video"""
    try:
        video_tasks = [
            (task_id, progress)
            for task_id, progress in task_progress.items()
            if video_id in task_id or video_id in str(progress.get("video_path", ""))
        ]

        if not video_tasks:
            videos_path = settings.get_videos_path()
            video_path = videos_path / video_id

            if not video_path.exists():
                raise HTTPException(status_code=404, detail="Video not found")

            srt_path = video_path.with_suffix(".srt")
            if srt_path.exists():
                return ProcessingStatus(
                    status="completed",
                    progress=100.0,
                    current_step="Processing completed",
                    message="Video has been fully processed",
                    subtitle_path=str(srt_path.relative_to(videos_path)),
                )
            else:
                return ProcessingStatus(
                    status="completed",
                    progress=0.0,
                    current_step="Not processed",
                    message="Video has not been processed yet",
                )

        _latest_task_id, latest_progress = video_tasks[-1]
        return latest_progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status for {video_id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting video status: {e!s}") from e


@router.post("/upload", name="upload_video_generic")
async def upload_video_generic(
    video_file: UploadFile = File(...), current_user: User = Depends(current_active_user), series: str = "Default"
):
    """Upload a new video file (generic endpoint) - Requires authentication"""
    return await upload_video(series, video_file, current_user)


def _validate_series_name(series: str) -> str:
    """Validate and sanitize series name to prevent path traversal"""
    safe_series = FileSecurityValidator.sanitize_filename(series)
    if safe_series != series or ".." in series or "/" in series or "\\" in series:
        raise HTTPException(status_code=400, detail="Invalid series name")
    return safe_series


async def _validate_video_file_upload(video_file: UploadFile) -> Path:
    """Validate uploaded video file for security"""
    allowed_extensions = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
    try:
        return await FileSecurityValidator.validate_file_upload(video_file, allowed_extensions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


async def _write_video_file(video_file: UploadFile, destination: Path) -> None:
    """Write uploaded video file in chunks for memory efficiency"""
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks

    with open(destination, "wb") as buffer:
        while True:
            chunk = await video_file.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer.write(chunk)


def _build_video_info_response(destination: Path, safe_series: str) -> VideoInfo:
    """Build VideoInfo response from uploaded video metadata"""
    video_service = VideoService(None, None)
    episode_info = video_service._parse_episode_filename(destination.stem)

    return VideoInfo(
        series=safe_series,
        season=episode_info.get("season", "1"),
        episode=episode_info.get("episode", "Unknown"),
        title=episode_info.get("title", destination.stem),
        path=str(destination.relative_to(settings.get_videos_path())),
        has_subtitles=False,
        duration=0,
    )


@router.post("/upload/{series}", name="upload_video_to_series")
async def upload_video(
    series: str, video_file: UploadFile = File(...), current_user: User = Depends(current_active_user)
):
    """
    Upload a new video file to a series - Requires authentication
    Uses FileSecurityValidator for secure file handling with path traversal prevention
    """
    try:
        safe_series = _validate_series_name(series)
        safe_path = await _validate_video_file_upload(video_file)

        series_path = settings.get_videos_path() / safe_series
        series_path.mkdir(parents=True, exist_ok=True)

        final_path = FileSecurityValidator.get_safe_upload_path(video_file.filename, preserve_name=True)
        final_destination = series_path / final_path.name

        if final_destination.exists():
            raise HTTPException(status_code=409, detail="File already exists")

        await _write_video_file(video_file, final_destination)

        if safe_path.exists() and safe_path != final_destination:
            safe_path.unlink(missing_ok=True)

        logger.info(f"[SECURITY] Uploaded video: {final_destination}")

        return _build_video_info_response(final_destination, safe_series)

    except HTTPException:
        raise
    except (OSError, PermissionError) as e:
        logger.error(f"Error uploading video: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading video: {e!s}") from e


def parse_episode_filename(filename: str) -> dict[str, str | None]:
    """
    Parse episode information from filename.

    Args:
        filename: The filename to parse (without extension)

    Returns:
        Dict containing episode, season, and title information
    """
    video_service = VideoService(None, None)
    return video_service._parse_episode_filename(filename)
