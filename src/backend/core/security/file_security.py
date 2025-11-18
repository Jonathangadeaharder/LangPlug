"""
File security validation module
Prevents path traversal attacks and validates file uploads
"""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile


class FileSecurityValidator:
    """
    Prevent path traversal attacks and validate file security

    Protects against:
    - Path traversal (.., /, etc.)
    - Malicious file extensions
    - Oversized files
    - Files outside allowed directories
    """

    # Allowed upload directory (configurable via environment)
    ALLOWED_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads")).resolve()

    # Allowed file extensions
    ALLOWED_EXTENSIONS: set[str] = {
        # Video formats
        ".mp4",
        ".webm",
        ".mkv",
        ".avi",
        ".mov",
        # Subtitle formats
        ".srt",
        ".vtt",
        ".sub",
        # Image formats
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        # Document formats
        ".pdf",
        ".txt",
    }

    # Maximum file size (500 MB)
    MAX_FILE_SIZE = 500 * 1024 * 1024

    @classmethod
    def validate_file_path(cls, file_path: str) -> Path:
        """
        Validate and sanitize file path.

        Args:
            file_path: File path to validate

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is invalid or contains traversal attempts
        """
        # Convert to Path and resolve to absolute path
        try:
            path = Path(file_path).resolve()
        except (ValueError, RuntimeError) as e:
            raise ValueError(f"Invalid file path: {e}") from e

        # Check for path traversal attempts
        if ".." in file_path or file_path.startswith("/") or file_path.startswith("\\"):
            raise ValueError("Path traversal attempt detected")

        # Ensure path is within allowed directory
        try:
            # Check if path is relative to allowed directory
            path.relative_to(cls.ALLOWED_UPLOAD_DIR)
        except ValueError as e:
            raise ValueError(f"Path {path} is outside allowed directory {cls.ALLOWED_UPLOAD_DIR}") from e

        return path

    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """
        Validate file extension against whitelist

        Args:
            filename: Filename to check

        Returns:
            True if extension is allowed, False otherwise
        """
        ext = Path(filename).suffix.lower()
        return ext in cls.ALLOWED_EXTENSIONS

    @classmethod
    async def validate_file_upload(cls, file: UploadFile, allowed_extensions: set[str] | None = None) -> Path:
        """
        Validate uploaded file for security

        Args:
            file: FastAPI UploadFile object
            allowed_extensions: Optional custom set of allowed extensions

        Returns:
            Safe file path for storage

        Raises:
            ValueError: If file fails validation
        """
        if not file.filename:
            raise ValueError("No filename provided")

        # Use custom extensions if provided, otherwise use defaults
        extensions = allowed_extensions or cls.ALLOWED_EXTENSIONS

        # Validate extension
        ext = Path(file.filename).suffix.lower()
        if ext not in extensions:
            raise ValueError(f"File type not allowed: {ext}. Allowed types: {', '.join(extensions)}")

        # Generate safe filename with UUID
        safe_filename = f"{uuid.uuid4()}{ext}"
        safe_path = cls.ALLOWED_UPLOAD_DIR / safe_filename

        # Ensure upload directory exists
        cls.ALLOWED_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Check file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > cls.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size} bytes (max {cls.MAX_FILE_SIZE} bytes / {cls.MAX_FILE_SIZE // (1024 * 1024)} MB)"
            )

        if file_size == 0:
            raise ValueError("File is empty")

        return safe_path

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename by removing dangerous characters

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove directory separators and traversal attempts
        filename = filename.replace("/", "").replace("\\", "").replace("..", "")

        # Remove null bytes and other dangerous characters
        filename = filename.replace("\x00", "")

        # Keep only alphanumeric, dash, underscore, and dot
        import re

        filename = re.sub(r"[^\w\s\-\.]", "", filename)

        # Limit length
        if len(filename) > 255:
            # Keep extension
            ext = Path(filename).suffix
            name = Path(filename).stem[:250]
            filename = f"{name}{ext}"

        return filename

    @classmethod
    def get_safe_upload_path(cls, original_filename: str, preserve_name: bool = False) -> Path:
        """
        Generate safe upload path

        Args:
            original_filename: Original filename from upload
            preserve_name: If True, sanitize and use original name; if False, generate UUID

        Returns:
            Safe Path object for file storage
        """
        ext = Path(original_filename).suffix.lower()

        if not ext:
            raise ValueError("File has no extension")

        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension {ext} not allowed")

        # Ensure upload directory exists
        cls.ALLOWED_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        if preserve_name:
            # Sanitize original filename
            safe_name = cls.sanitize_filename(Path(original_filename).stem)
            filename = f"{safe_name}{ext}"

            # Check if file already exists, add counter if needed
            safe_path = cls.ALLOWED_UPLOAD_DIR / filename
            counter = 1
            while safe_path.exists():
                filename = f"{safe_name}_{counter}{ext}"
                safe_path = cls.ALLOWED_UPLOAD_DIR / filename
                counter += 1
        else:
            # Generate UUID-based filename
            filename = f"{uuid.uuid4()}{ext}"
            safe_path = cls.ALLOWED_UPLOAD_DIR / filename

        return safe_path


def validate_upload_security(file_path: str) -> bool:
    """
    Convenience function to validate file path security

    Args:
        file_path: Path to validate

    Returns:
        True if valid, raises ValueError if invalid
    """
    FileSecurityValidator.validate_file_path(file_path)
    return True


def get_safe_filename(original_filename: str) -> str:
    """
    Convenience function to sanitize filename

    Args:
        original_filename: Original filename

    Returns:
        Sanitized filename
    """
    return FileSecurityValidator.sanitize_filename(original_filename)
