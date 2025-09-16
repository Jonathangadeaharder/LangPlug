"""Authentication models and data classes"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.models import User


@dataclass
class AuthSession:
    """Represents a user session"""
    session_token: str
    user: "User"
    expires_at: datetime
    created_at: datetime


class AuthenticationError(Exception):
    """Base exception for authentication errors"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    pass


class UserAlreadyExistsError(AuthenticationError):
    """Raised when trying to register a user that already exists"""
    pass


class SessionExpiredError(AuthenticationError):
    """Raised when a session token has expired"""
    pass