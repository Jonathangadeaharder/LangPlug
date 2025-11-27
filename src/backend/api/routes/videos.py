"""
Video management API routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.error_handlers import handle_api_errors, raise_bad_request, raise_conflict, raise_not_found
from core.exceptions import EpisodeNotFoundError, SeriesNotFoundError, VideoNotFoundError
from api.models.processing import ProcessingStatus
from api.models.video import VideoInfo
from api.models.vocabulary import VocabularyWord
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
    """
    Retrieve list of all available videos and series for the current user.
    """
    return video_service.get_available_videos()


@router.get("/subtitles/{subtitle_path:path}", name="get_subtitles")
@handle_api_errors("serving subtitle file")
async def get_subtitles(
    subtitle_path: str,
    current_user: User = Depends(current_active_user),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Serve subtitle files (SRT format) for video playback.
    """
    logger.info(f"Serving subtitles: {subtitle_path}")

    subtitle_file = video_service.get_subtitle_file_path(subtitle_path)

    # Verify file exists and is readable
    if not subtitle_file.exists():
        logger.warning(f"Subtitle file not found: {subtitle_file}")
        raise_not_found("Subtitle file", subtitle_path)

    if not subtitle_file.is_file():
        logger.warning(f"Subtitle path is not a file: {subtitle_file}")
        raise_not_found("Subtitle file", subtitle_path)

    logger.info(f"Successfully serving subtitle file: {subtitle_file}")
    return FileResponse(
        path=str(subtitle_file), media_type="text/plain", headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@router.get(
    "/{series}/{episode}",
    name="stream_video",
    responses={
        200: {"description": "Full video content"},
        206: {"description": "Partial video content (range request)"},
        401: {"description": "Invalid or missing authentication token"},
        404: {"description": "Video file not accessible"},
    },
)
@handle_api_errors("streaming video file")
async def stream_video(
    series: str,
    episode: str,
    current_user: User = Depends(get_user_from_query_token),
    video_service: VideoService = Depends(get_video_service),
):
    """Stream video file - Requires authentication"""
    try:
        video_file = video_service.get_video_file_path(series, episode)
    except SeriesNotFoundError:
        raise_not_found("Series", series)
    except EpisodeNotFoundError:
        raise_not_found("Episode", f"{episode} in series {series}")
    except Exception as e:
        # Map unexpected errors if any
        logger.error(f"Error finding video: {e}")
        raise_not_found("Video file", f"{series}/{episode}")

    if not video_file.exists():
        logger.error(f"Video file exists check failed: {video_file}")
        raise_not_found("Video file", f"{series}/{episode}")

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


@router.post("/subtitle/upload", name="upload_subtitle")
@handle_api_errors("uploading subtitle file")
async def upload_subtitle(
    video_path: str, subtitle_file: UploadFile = File(...), current_user: User = Depends(current_active_user)
):
    """
    Upload subtitle file for a video - Requires authentication
    Uses FileSecurityValidator for secure file handling
    """
    # Logic for subtitle upload is still partly in route due to direct file handling requirements
    # TODO: Move to SubtitleService in future refactoring
    from core.config import settings
    from core.file_security import FileSecurityValidator

    allowed_extensions = {".srt", ".vtt", ".sub"}
    try:
        await FileSecurityValidator.validate_file_upload(subtitle_file, allowed_extensions)
    except ValueError as e:
        raise_bad_request(str(e))

    content = await subtitle_file.read()

    videos_path = settings.get_videos_path()
    try:
        video_file_path = str(videos_path / video_path)
        FileSecurityValidator.validate_file_path(video_file_path)
        video_file = videos_path / video_path
    except ValueError as e:
        raise_bad_request(f"Invalid video path: {e}")

    if not video_file.exists():
        raise_not_found("Video file", video_path)

    subtitle_path = video_file.with_suffix(".srt")

    with open(subtitle_path, "wb") as buffer:
        buffer.write(content)

    logger.info(f"[SECURITY] Uploaded subtitle: {subtitle_path}")

    return {
        "success": True,
        "message": f"Subtitle uploaded for {video_path}",
        "subtitle_path": str(subtitle_path.relative_to(videos_path)),
    }


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
@handle_api_errors("extracting video vocabulary")
async def get_video_vocabulary(
    video_id: str,
    current_user: User = Depends(current_active_user),
    video_service: VideoService = Depends(get_video_service),
):
    """Get vocabulary words extracted from a video"""
    try:
        return video_service.get_video_vocabulary(video_id)
    except FileNotFoundError as e:
        raise_not_found("Video or Subtitles", video_id)


@router.get("/{video_id}/status", response_model=ProcessingStatus, name="get_video_status")
@handle_api_errors("getting video status")
async def get_video_status(
    video_id: str,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
    video_service: VideoService = Depends(get_video_service),
):
    """Get processing status for a video"""
    status = video_service.get_video_status(video_id, task_progress)
    if status is None:
        raise_not_found("Video", video_id)
    return ProcessingStatus(**status)


@router.post("/upload", name="upload_video_generic", response_model=VideoInfo)
async def upload_video_generic(
    video_file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    series: str = "Default",
    video_service: VideoService = Depends(get_video_service),
):
    """Upload a new video file (generic endpoint) - Requires authentication"""
    try:
        return await video_service.upload_video(series, video_file)
    except ValueError as e:
        raise_bad_request(str(e))
    except FileExistsError as e:
        raise_conflict("Video file", str(e))


@router.post("/upload/{series}", name="upload_video_to_series", response_model=VideoInfo, status_code=200, responses={
    200: {"description": "Video uploaded successfully", "model": VideoInfo},
    400: {"description": "Bad request - invalid video file or parameters"},
    401: {"description": "Unauthorized - authentication required"},
    409: {"description": "Conflict - video file already exists"},
})
@handle_api_errors("uploading video file")
async def upload_video(
    series: str,
    video_file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Upload a new video file to a series - Requires authentication
    """
    try:
        return await video_service.upload_video(series, video_file)
    except ValueError as e:
        raise_bad_request(str(e))
    except FileExistsError as e:
        raise_conflict("Video file", str(e))


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
