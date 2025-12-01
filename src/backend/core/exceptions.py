"""
Custom exceptions for LangPlug API

This module provides a hierarchy of domain exceptions that are HTTP-agnostic.
Service layer should use these exceptions, and the API layer (routes) should
catch and convert them to appropriate HTTP responses.

Exception Hierarchy:
    LangPlugException (base)
    ├── AuthenticationError (401)
    │   ├── InvalidCredentialsError
    │   └── SessionExpiredError
    ├── AuthorizationError (403)
    ├── ValidationError (422)
    ├── NotFoundError (404)
    │   ├── VideoNotFoundError
    │   ├── EpisodeNotFoundError
    │   └── VocabularyNotFoundError
    ├── ConflictError (409)
    │   └── ResourceExistsError
    ├── ServiceUnavailableError (503)
    ├── ProcessingError (500)
    └── ConfigurationError (500)
"""

from fastapi import status


class LangPlugException(Exception):  # noqa: N818
    """Base exception for LangPlug.

    All domain exceptions should inherit from this class.
    The status_code is used by exception handlers to generate HTTP responses.
    """

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(LangPlugException):
    """Base authentication related errors"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(LangPlugException):
    """Authorization related errors"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationError(LangPlugException):
    """Validation related errors"""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""

    def __init__(self, message: str = "Invalid credentials provided"):
        super().__init__(message)


class UserAlreadyExistsError(LangPlugException):
    """Raised when trying to register a user that already exists"""

    def __init__(self, message: str = "User already exists"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class SessionExpiredError(AuthenticationError):
    """Raised when a session token has expired"""

    def __init__(self, message: str = "Session has expired"):
        super().__init__(message)


class NotFoundError(LangPlugException):
    """Resource not found errors"""

    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status.HTTP_404_NOT_FOUND)


class ServiceUnavailableError(LangPlugException):
    """Service unavailable errors"""

    def __init__(self, service: str = "Service"):
        super().__init__(f"{service} is currently unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)


class ProcessingError(LangPlugException):
    """Processing related errors"""

    def __init__(self, message: str = "Processing failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfigurationError(LangPlugException):
    """Configuration related errors"""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


# Domain-specific NotFound exceptions
class VideoNotFoundError(NotFoundError):
    """Raised when a video file or series is not found"""

    def __init__(self, video_id: str, series: str | None = None):
        self.video_id = video_id
        self.series = series
        if series:
            message = f"Video '{video_id}' in series '{series}'"
        else:
            message = f"Video: {video_id}"
        super().__init__(message)


class EpisodeNotFoundError(NotFoundError):
    """Raised when an episode is not found in a series"""

    def __init__(self, episode: str, series: str):
        self.episode = episode
        self.series = series
        super().__init__(f"Episode '{episode}' in series '{series}'")


class SeriesNotFoundError(NotFoundError):
    """Raised when a video series/folder is not found"""

    def __init__(self, series: str):
        self.series = series
        super().__init__(f"Series '{series}'")


class SubtitleNotFoundError(NotFoundError):
    """Raised when subtitle file is not found"""

    def __init__(self, video_path: str):
        self.video_path = video_path
        super().__init__(f"Subtitles for video: {video_path}")


class VocabularyNotFoundError(NotFoundError):
    """Raised when vocabulary word is not found"""

    def __init__(self, word: str, language: str = "de"):
        self.word = word
        self.language = language
        super().__init__(f"Vocabulary word '{word}' in {language}")


# Conflict exceptions
class ConflictError(LangPlugException):
    """Base class for resource conflict errors (409)"""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class ResourceExistsError(ConflictError):
    """Raised when trying to create a resource that already exists"""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} already exists: {identifier}")


class FileExistsError(ConflictError):
    """Raised when trying to upload a file that already exists"""

    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"File already exists: {filename}")
