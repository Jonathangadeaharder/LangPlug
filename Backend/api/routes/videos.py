"""
Video management API routes
"""

import logging
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
    """Get list of available videos/series"""
    return video_service.get_available_videos()


@router.get("/subtitles/{subtitle_path:path}", name="get_subtitles")
async def get_subtitles(
    subtitle_path: str,
    current_user: User = Depends(current_active_user),
    video_service: VideoService = Depends(get_video_service),
):
    """Serve subtitle files - Requires authentication"""
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
        raise HTTPException(status_code=500, detail=f"Error serving subtitles: {e!s}")


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

        # Return video with proper headers for streaming
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
        raise HTTPException(status_code=500, detail=f"Error streaming video: {e!s}")


@router.post("/subtitle/upload", name="upload_subtitle")
async def upload_subtitle(
    video_path: str, subtitle_file: UploadFile = File(...), current_user: User = Depends(current_active_user)
):
    """Upload subtitle file for a video - Requires authentication"""
    try:
        # Validate file type
        if not subtitle_file.filename.endswith((".srt", ".vtt", ".sub")):
            raise HTTPException(status_code=400, detail="File must be a subtitle file (.srt, .vtt, or .sub)")

        # Read content and validate size
        content = await subtitle_file.read()
        file_size_kb = len(content) / 1024

        MAX_SUBTITLE_SIZE_KB = 1024  # 1MB limit for subtitles
        if file_size_kb > MAX_SUBTITLE_SIZE_KB:
            raise HTTPException(
                status_code=413,
                detail=f"Subtitle file too large. Maximum size is {MAX_SUBTITLE_SIZE_KB}KB, got {file_size_kb:.1f}KB",
            )

        # Get video file path
        videos_path = settings.get_videos_path()
        video_file = videos_path / video_path

        if not video_file.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        # Save subtitle with same name as video
        subtitle_path = video_file.with_suffix(".srt")

        # Write uploaded file (content already read for size validation)
        with open(subtitle_path, "wb") as buffer:
            buffer.write(content)

        logger.info(f"Uploaded subtitle: {subtitle_path}")

        return {
            "success": True,
            "message": f"Subtitle uploaded for {video_path}",
            "subtitle_path": str(subtitle_path.relative_to(videos_path)),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading subtitle: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading subtitle: {e!s}")


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
        # Convert video_id to video path
        videos_path = settings.get_videos_path()
        video_path = videos_path / video_id

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")

        # Check for corresponding subtitle file
        srt_path = video_path.with_suffix(".srt")
        if not srt_path.exists():
            raise HTTPException(status_code=404, detail="Subtitles not found for this video")

        # Extract vocabulary using the existing vocabulary extraction logic
        from api.routes.vocabulary import extract_blocking_words_for_segment

        # Extract vocabulary for the entire video (0 to large duration)
        vocabulary_words = await extract_blocking_words_for_segment(str(srt_path), 0, 999999, current_user.id)

        logger.info(f"Extracted {len(vocabulary_words)} vocabulary words for video {video_id}")
        return vocabulary_words

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting vocabulary for video {video_id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error extracting vocabulary: {e!s}")


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
        # Look for any processing tasks related to this video
        video_tasks = [
            (task_id, progress)
            for task_id, progress in task_progress.items()
            if video_id in task_id or video_id in str(progress.get("video_path", ""))
        ]

        if not video_tasks:
            # No active processing, check if video exists and has been processed
            videos_path = settings.get_videos_path()
            video_path = videos_path / video_id

            if not video_path.exists():
                raise HTTPException(status_code=404, detail="Video not found")

            # Check if subtitles exist (indicates processing completed)
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

        # Return the most recent task status
        _latest_task_id, latest_progress = video_tasks[-1]
        return latest_progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status for {video_id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting video status: {e!s}")


@router.post("/upload", name="upload_video_generic")
async def upload_video_generic(
    video_file: UploadFile = File(...), current_user: User = Depends(current_active_user), series: str = "Default"
):
    """Upload a new video file (generic endpoint) - Requires authentication"""
    return await upload_video(series, video_file, current_user)


@router.post("/upload/{series}", name="upload_video_to_series")
async def upload_video(
    series: str, video_file: UploadFile = File(...), current_user: User = Depends(current_active_user)
):
    """Upload a new video file to a series - Requires authentication"""
    try:
        # Validate file type
        if not video_file.content_type or not video_file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="File must be a video")

        # Get series directory
        series_path = settings.get_videos_path() / series
        series_path.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        safe_filename = video_file.filename
        if not safe_filename or not safe_filename.endswith((".mp4", ".avi", ".mkv", ".mov")):
            raise HTTPException(status_code=400, detail="Invalid video file format")

        # Save file
        file_path = series_path / safe_filename

        # Check if file already exists
        if file_path.exists():
            raise HTTPException(status_code=409, detail="File already exists")

        # Read and validate file size in chunks
        total_size = 0
        MAX_VIDEO_SIZE_MB = 500  # 500MB limit for videos
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks
        max_size_bytes = MAX_VIDEO_SIZE_MB * 1024 * 1024

        with open(file_path, "wb") as buffer:
            while True:
                chunk = await video_file.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > max_size_bytes:
                    # Delete partially written file
                    buffer.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video file too large. Maximum size is {MAX_VIDEO_SIZE_MB}MB, got {total_size / (1024 * 1024):.1f}MB",
                    )

                buffer.write(chunk)

        logger.info(f"Uploaded video: {file_path}")

        # Return video info
        video_service = VideoService(None, None)  # We only need the parsing method
        episode_info = video_service._parse_episode_filename(file_path.stem)

        return VideoInfo(
            series=series,
            season=episode_info.get("season", "1"),
            episode=episode_info.get("episode", "Unknown"),
            title=episode_info.get("title", file_path.stem),
            path=str(file_path.relative_to(settings.get_videos_path())),
            has_subtitles=False,  # New uploads won't have subtitles initially
            duration=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading video: {e!s}")


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
