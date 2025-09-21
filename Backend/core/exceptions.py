"""
Custom exceptions for LangPlug API
"""
from fastapi import status


class LangPlugException(Exception):
    """Base exception for LangPlug"""
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
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_CONTENT)


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
