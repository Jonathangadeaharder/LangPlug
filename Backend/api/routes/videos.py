"""
Video management API routes
"""
import logging
from pathlib import Path
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, PlainTextResponse

from ..models.video import VideoInfo
from core.dependencies import get_current_user, get_auth_service
from core.config import settings
from core.constants import MAX_VIDEO_SIZE_MB, MAX_SUBTITLE_SIZE_KB, CHUNK_SIZE
from services.authservice.auth_service import AuthUser, AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])


def parse_episode_filename(filename: str) -> Dict[str, str]:
    """Parse episode information from filename"""
    # Simple parsing - can be enhanced
    parts = filename.split()
    episode_info = {"title": filename}
    
    for i, part in enumerate(parts):
        if "episode" in part.lower() and i + 1 < len(parts):
            episode_info["episode"] = parts[i + 1]
        elif "staffel" in part.lower() and i + 1 < len(parts):
            episode_info["season"] = parts[i + 1]
    
    return episode_info


@router.get("", response_model=List[VideoInfo])
async def get_available_videos(current_user: AuthUser = Depends(get_current_user)):
    """Get list of available videos/series"""
    try:
        videos_path = settings.get_videos_path()
        videos = []
        
        logger.info(f"Scanning for videos in: {videos_path}")
        
        if not videos_path.exists():
            logger.warning(f"Videos path does not exist: {videos_path}")
            return videos
        
        # First, scan for video files directly in videos_path
        for video_file in videos_path.glob("*.mp4"):
            # Check for corresponding subtitle file
            srt_file = video_file.with_suffix(".srt")
            has_subtitles = srt_file.exists()
            
            # Extract episode information from filename
            filename = video_file.stem
            episode_info = parse_episode_filename(filename)
            
            video_info = VideoInfo(
                series="Default",
                season=episode_info.get("season", "1"),
                episode=episode_info.get("episode", filename),
                title=episode_info.get("title", filename),
                path=str(video_file.relative_to(videos_path)),
                has_subtitles=has_subtitles
            )
            videos.append(video_info)
            logger.debug(f"Added video: {video_info.title}")
        
        # Also scan for series directories
        for series_dir in videos_path.iterdir():
            if series_dir.is_dir():
                series_name = series_dir.name
                logger.debug(f"Found series directory: {series_name}")
                
                # Scan for video files
                for video_file in series_dir.glob("*.mp4"):
                    # Check for corresponding subtitle file
                    srt_file = video_file.with_suffix(".srt")
                    has_subtitles = srt_file.exists()
                    
                    # Extract episode information from filename
                    filename = video_file.stem
                    episode_info = parse_episode_filename(filename)
                    
                    video_info = VideoInfo(
                        series=series_name,
                        season=episode_info.get("season", "1"),
                        episode=episode_info.get("episode", "Unknown"),
                        title=episode_info.get("title", filename),
                        path=str(video_file.relative_to(videos_path)),
                        has_subtitles=has_subtitles
                    )
                    videos.append(video_info)
                    logger.debug(f"Added video: {video_info.title}")
        
        logger.info(f"Found {len(videos)} videos")
        return videos
        
    except Exception as e:
        logger.error(f"Error scanning videos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scanning videos: {str(e)}")


@router.get("/{series}/{episode}")
async def stream_video(
    series: str, 
    episode: str,
    token: str = Query(None, description="Authentication token for video streaming"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Stream video file - Supports token-based authentication via query parameter"""
    try:
        # Validate token if provided
        if token:
            try:
                await auth_service.validate_token(token)
            except Exception as e:
                logger.warning(f"Invalid token provided for video streaming: {e}")
                # For now, allow access even with invalid token to support development
                pass
        # No authentication required for now to support development
        videos_path = settings.get_videos_path() / series
        logger.info(f"Looking for video in: {videos_path}")
        
        if not videos_path.exists():
            logger.warning(f"Series path does not exist: {videos_path}")
            raise HTTPException(status_code=404, detail=f"Series '{series}' not found")
        
        # Find matching video file
        found_files = []
        for video_file in videos_path.glob("*.mp4"):
            found_files.append(video_file.name)
            # More flexible matching - check if episode number is in filename
            # This handles both "1" matching "Episode 1" and full episode names
            filename_lower = video_file.name.lower()
            episode_lower = episode.lower()
            
            # Try different matching patterns
            matches = (
                f"episode {episode_lower}" in filename_lower or  # "episode 1"
                f"episode_{episode_lower}" in filename_lower or  # "episode_1"
                f"e{episode_lower}" in filename_lower or         # "e1"
                episode_lower in filename_lower                  # direct match
            )
            
            if matches:
                logger.info(f"Found matching video: {video_file} for episode: {episode}")
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
                        "Access-Control-Allow-Headers": "Range"
                    }
                )
                return response
        
        logger.warning(f"No matching video found for episode '{episode}'. Available files: {found_files}")
        raise HTTPException(
            status_code=404, 
            detail=f"Episode '{episode}' not found in series '{series}'. Available: {found_files}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stream_video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error streaming video: {str(e)}")


@router.get("/subtitles/{subtitle_path:path}")
async def get_subtitles(
    subtitle_path: str,
    token: str = Query(None, description="Authentication token for subtitle access")
):
    """Serve subtitle files - Supports token-based authentication via query parameter"""
    try:
        # No authentication required for now to support development
        logger.info(f"Serving subtitles: {subtitle_path}")
        
        # CRITICAL FIX: Handle Windows absolute paths by converting to relative paths
        # The frontend may send Windows absolute paths like C:\Users\...\videos\Superstore\file.srt
        videos_root = settings.get_videos_path()
        
        if subtitle_path.startswith(("C:", "D:", "/mnt/c/", "/mnt/d/")) or "\\" in subtitle_path:
            # This is an absolute Windows path - convert to relative
            path_obj = Path(subtitle_path.replace("\\", "/"))
            
            # Find the videos directory in the path and get the relative part
            path_parts = path_obj.parts
            try:
                videos_index = next(i for i, part in enumerate(path_parts) if part.lower() == "videos")
                relative_path = Path(*path_parts[videos_index + 1:])
                subtitle_file = videos_root / relative_path
                logger.info(f"Converted absolute path {subtitle_path} to relative: {relative_path}")
            except (StopIteration, IndexError):
                logger.warning(f"Could not find 'videos' directory in path: {subtitle_path}")
                subtitle_file = videos_root / Path(subtitle_path).name
        else:
            # Regular relative path handling
            subtitle_file = videos_root / subtitle_path
        
        logger.info(f"Looking for subtitle file at: {subtitle_file}")
        
        if not subtitle_file.exists():
            logger.error(f"Subtitle file not found: {subtitle_file}")
            raise HTTPException(status_code=404, detail=f"Subtitle file not found: {subtitle_file}")
        
        # Read and return the SRT content
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return PlainTextResponse(content, media_type="text/plain")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving subtitles: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error serving subtitles: {str(e)}")


@router.post("/subtitle/upload")
async def upload_subtitle(
    video_path: str,
    subtitle_file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user)
):
    """Upload subtitle file for a video"""
    try:
        # Validate file type
        if not subtitle_file.filename.endswith(('.srt', '.vtt', '.sub')):
            raise HTTPException(status_code=400, detail="File must be a subtitle file (.srt, .vtt, or .sub)")
        
        # Read content and validate size
        content = await subtitle_file.read()
        file_size_kb = len(content) / 1024
        
        if file_size_kb > MAX_SUBTITLE_SIZE_KB:
            raise HTTPException(
                status_code=413,
                detail=f"Subtitle file too large. Maximum size is {MAX_SUBTITLE_SIZE_KB}KB, got {file_size_kb:.1f}KB"
            )
        
        # Get video file path
        videos_path = settings.get_videos_path()
        video_file = videos_path / video_path
        
        if not video_file.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Save subtitle with same name as video
        subtitle_path = video_file.with_suffix('.srt')
        
        # Write uploaded file (content already read for size validation)
        with open(subtitle_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"Uploaded subtitle: {subtitle_path}")
        
        return {
            "success": True,
            "message": f"Subtitle uploaded for {video_path}",
            "subtitle_path": str(subtitle_path.relative_to(videos_path))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading subtitle: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading subtitle: {str(e)}")


@router.post("/upload/{series}")
async def upload_video(
    series: str,
    video_file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user)
):
    """Upload a new video file to a series"""
    try:
        # Validate file type
        if not video_file.content_type or not video_file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Get series directory
        series_path = settings.get_videos_path() / series
        series_path.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename
        safe_filename = video_file.filename
        if not safe_filename or not safe_filename.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            raise HTTPException(status_code=400, detail="Invalid video file format")
        
        # Save file
        file_path = series_path / safe_filename
        
        # Check if file already exists
        if file_path.exists():
            raise HTTPException(status_code=409, detail="File already exists")
        
        # Read and validate file size in chunks
        total_size = 0
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
                        detail=f"Video file too large. Maximum size is {MAX_VIDEO_SIZE_MB}MB, got {total_size/(1024*1024):.1f}MB"
                    )
                
                buffer.write(chunk)
        
        logger.info(f"Uploaded video: {file_path}")
        
        # Return video info
        episode_info = parse_episode_filename(file_path.stem)
        return VideoInfo(
            series=series,
            season=episode_info.get("season", "1"),
            episode=episode_info.get("episode", "Unknown"),
            title=episode_info.get("title", file_path.stem),
            path=str(file_path.relative_to(settings.get_videos_path())),
            has_subtitles=False  # New uploads won't have subtitles initially
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")