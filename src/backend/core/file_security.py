"""
File Security Validation

Provides comprehensive file security validation for uploads, including:
- Path traversal prevention
- File extension validation
- Filename sanitization
- Safe upload path generation
"""

import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from core.config import settings


class FileSecurityValidator:
    """
    File security validation and sanitization utilities

    Prevents common file upload vulnerabilities:
    - Path traversal attacks (../, absolute paths)
    - Malicious file extensions
    - Filename injection (null bytes, Unicode attacks)
    - Oversized file uploads
    """

    # Allowed file extensions by category
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov"}
    ALLOWED_SUBTITLE_EXTENSIONS = {".srt", ".vtt"}
    ALLOWED_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_SUBTITLE_EXTENSIONS

    # Maximum file size: 500 MB
    MAX_FILE_SIZE = 500 * 1024 * 1024

    # Upload directory (can be patched in tests) - lazily initialized
    ALLOWED_UPLOAD_DIR: Path | None = None

    @classmethod
    def get_upload_dir(cls) -> Path:
        """Get upload directory (lazily initialized)"""
        if cls.ALLOWED_UPLOAD_DIR is None:
            cls.ALLOWED_UPLOAD_DIR = settings.get_videos_path()
        return cls.ALLOWED_UPLOAD_DIR

    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """
        Validate if file extension is allowed

        Args:
            filename: Filename to validate

        Returns:
            True if extension is allowed, False otherwise

        Example:
            >>> FileSecurityValidator.validate_file_extension("video.mp4")
            True
            >>> FileSecurityValidator.validate_file_extension("malware.exe")
            False
        """
        if not filename or "." not in filename:
            return False

        # Get extension (case-insensitive)
        extension = Path(filename).suffix.lower()
        return extension in FileSecurityValidator.ALLOWED_EXTENSIONS

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitize filename to prevent security issues

        Removes:
        - Path separators (/, \\)
        - Parent directory references (..)
        - Null bytes
        - Unicode control characters
        - Special characters except: - _ .

        Args:
            filename: Original filename
            max_length: Maximum filename length (default: 255)

        Returns:
            Sanitized filename

        Example:
            >>> FileSecurityValidator.sanitize_filename("../etc/passwd")
            'etcpasswd'
            >>> FileSecurityValidator.sanitize_filename("file\\x00.exe")
            'file.exe'
        """
        if not filename:
            return "unnamed"

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Remove Unicode control characters (including right-to-left override)
        filename = "".join(char for char in filename if not (ord(char) < 32 or 0x202E <= ord(char) <= 0x202F))

        # Remove path separators and parent directory references
        filename = filename.replace("/", "").replace("\\", "").replace("..", "")

        # Keep only alphanumeric, dash, underscore, and dot
        filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

        # Limit length while preserving extension
        if len(filename) > max_length:
            name_part = Path(filename).stem
            ext_part = Path(filename).suffix
            # Reserve space for extension + 1 char for name
            max_name_length = max_length - len(ext_part)
            filename = name_part[:max_name_length] + ext_part

        return filename if filename else "unnamed"

    @staticmethod
    def validate_file_path(file_path: str) -> None:
        """
        Validate file path to prevent path traversal attacks

        Args:
            file_path: File path to validate

        Raises:
            ValueError: If path contains traversal attempts

        Example:
            >>> FileSecurityValidator.validate_file_path("videos/video.mp4")
            None  # Success
            >>> FileSecurityValidator.validate_file_path("../etc/passwd")
            ValueError: Path traversal attempt detected
        """
        # Check for parent directory traversal
        if ".." in file_path:
            raise ValueError("Path traversal attempt detected: parent directory reference")

        # Check for absolute paths (Unix and Windows)
        if file_path.startswith("/") or (len(file_path) > 1 and file_path[1] == ":"):
            raise ValueError("Path traversal attempt detected: absolute path not allowed")

        # Check for backslash (Windows path separator)
        if "\\" in file_path:
            raise ValueError("Path traversal attempt detected: backslash not allowed")

    @staticmethod
    async def validate_file_upload(file: UploadFile, allowed_extensions: set[str] | None = None) -> Path:
        """
        Validate uploaded file for security and constraints

        Args:
            file: FastAPI UploadFile object
            allowed_extensions: Set of allowed extensions (default: all allowed types)

        Returns:
            Path object with validated extension

        Raises:
            ValueError: If file validation fails

        Example:
            >>> mock_file = UploadFile(filename="video.mp4")
            >>> await FileSecurityValidator.validate_file_upload(mock_file)
            Path('video.mp4')
        """
        # Check filename exists
        if not file.filename:
            raise ValueError("No filename provided")

        # Use default allowed extensions if not specified
        if allowed_extensions is None:
            allowed_extensions = FileSecurityValidator.ALLOWED_EXTENSIONS

        # Validate extension
        extension = Path(file.filename).suffix.lower()
        if extension not in allowed_extensions:
            raise ValueError(f"File type not allowed: {extension}")

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size == 0:
            raise ValueError("File is empty")

        if file_size > FileSecurityValidator.MAX_FILE_SIZE:
            max_mb = FileSecurityValidator.MAX_FILE_SIZE / (1024 * 1024)
            raise ValueError(f"File too large. Maximum size: {max_mb:.0f} MB")

        return Path(file.filename)

    @staticmethod
    def get_safe_upload_path(filename: str, preserve_name: bool = False) -> Path:
        """
        Generate safe upload path with sanitized filename

        Args:
            filename: Original filename
            preserve_name: If True, preserve sanitized original name. If False, use UUID.

        Returns:
            Path object in allowed upload directory

        Raises:
            ValueError: If file has no extension or disallowed extension

        Example:
            >>> FileSecurityValidator.get_safe_upload_path("video.mp4")
            Path('/uploads/550e8400-e29b-41d4-a716-446655440000.mp4')
            >>> FileSecurityValidator.get_safe_upload_path("my_video.mp4", preserve_name=True)
            Path('/uploads/my_video.mp4')
        """
        # Validate extension
        extension = Path(filename).suffix.lower()
        if not extension:
            raise ValueError("File has no extension")

        if extension not in FileSecurityValidator.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{extension}' is not allowed")

        # Generate safe filename
        if preserve_name:
            # Sanitize and preserve original name
            safe_name = FileSecurityValidator.sanitize_filename(Path(filename).stem)
            safe_filename = f"{safe_name}{extension}"
        else:
            # Use UUID for guaranteed uniqueness
            safe_filename = f"{uuid.uuid4()}{extension}"

        return FileSecurityValidator.get_upload_dir() / safe_filename
