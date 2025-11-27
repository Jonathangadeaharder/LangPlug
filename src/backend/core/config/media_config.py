"""
Centralized media configuration for video and subtitle handling.

Provides single source of truth for:
- Allowed video extensions
- Allowed subtitle extensions
- MIME type mappings
- File size limits
"""

from typing import Final

# Video file extensions - used by VideoService, filtering_routes, file validators
VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".mp4",
    ".mkv",
    ".avi",
    ".webm",
    ".mov",
    ".m4v",
    ".wmv",
    ".flv",
})

# Subtitle file extensions
SUBTITLE_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".srt",
    ".vtt",
    ".sub",
    ".ass",
    ".ssa",
})

# Audio file extensions for transcription
AUDIO_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".mp3",
    ".wav",
    ".flac",
    ".m4a",
    ".ogg",
    ".aac",
})

# MIME type mappings
VIDEO_MIME_TYPES: Final[dict[str, str]] = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".wmv": "video/x-ms-wmv",
    ".flv": "video/x-flv",
}

SUBTITLE_MIME_TYPES: Final[dict[str, str]] = {
    ".srt": "text/plain",
    ".vtt": "text/vtt",
    ".sub": "text/plain",
    ".ass": "text/plain",
    ".ssa": "text/plain",
}

# File size limits (in bytes)
MAX_VIDEO_SIZE: Final[int] = 2 * 1024 * 1024 * 1024  # 2GB
MAX_SUBTITLE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE: Final[int] = 500 * 1024 * 1024  # 500MB


def is_valid_video_extension(extension: str) -> bool:
    """Check if file extension is a valid video format."""
    return extension.lower() in VIDEO_EXTENSIONS


def is_valid_subtitle_extension(extension: str) -> bool:
    """Check if file extension is a valid subtitle format."""
    return extension.lower() in SUBTITLE_EXTENSIONS


def is_valid_audio_extension(extension: str) -> bool:
    """Check if file extension is a valid audio format."""
    return extension.lower() in AUDIO_EXTENSIONS


def get_video_mime_type(extension: str) -> str:
    """Get MIME type for video extension, defaults to application/octet-stream."""
    return VIDEO_MIME_TYPES.get(extension.lower(), "application/octet-stream")


def get_subtitle_mime_type(extension: str) -> str:
    """Get MIME type for subtitle extension, defaults to text/plain."""
    return SUBTITLE_MIME_TYPES.get(extension.lower(), "text/plain")


__all__ = [
    "AUDIO_EXTENSIONS",
    "MAX_AUDIO_SIZE",
    "MAX_SUBTITLE_SIZE",
    "MAX_VIDEO_SIZE",
    "SUBTITLE_EXTENSIONS",
    "SUBTITLE_MIME_TYPES",
    "VIDEO_EXTENSIONS",
    "VIDEO_MIME_TYPES",
    "get_subtitle_mime_type",
    "get_video_mime_type",
    "is_valid_audio_extension",
    "is_valid_subtitle_extension",
    "is_valid_video_extension",
]
