"""
Media validation utilities for video files
"""
import mimetypes
from pathlib import Path

# Common video file extensions
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
    '.m4v', '.3gp', '.3g2', '.mpg', '.mpeg', '.ts', '.mts'
}

# Common video MIME types
VIDEO_MIME_TYPES = {
    'video/mp4', 'video/avi', 'video/x-matroska', 'video/quicktime',
    'video/x-ms-wmv', 'video/x-flv', 'video/webm', 'video/3gpp',
    'video/3gpp2', 'video/mpeg', 'video/mp2t'
}

def is_valid_video_file(file_path: str) -> bool:
    """
    Check if a file is a valid video file based on extension and MIME type.
    
    Args:
        file_path (str): Path to the file to validate
        
    Returns:
        bool: True if the file is a valid video file, False otherwise
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False
    
    # Check file extension
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return True
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type and mime_type in VIDEO_MIME_TYPES:
        return True
    
    return False

def get_video_extensions() -> set:
    """
    Get the set of supported video file extensions.
    
    Returns:
        set: Set of supported video file extensions
    """
    return VIDEO_EXTENSIONS

def get_video_mime_types() -> set:
    """
    Get the set of supported video MIME types.
    
    Returns:
        set: Set of supported video MIME types
    """
    return VIDEO_MIME_TYPES