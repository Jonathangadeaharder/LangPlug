"""Authentication models and data classes"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

# Import unified exceptions from core module
from core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError, 
    UserAlreadyExistsError,
    SessionExpiredError
)

if TYPE_CHECKING:
    from database.models import User


@dataclass
class AuthUser:
    """Represents an authenticated user"""
    id: str
    username: str
    is_admin: bool = False
    is_active: bool = True
    created_at: str = ""
    native_language: str = "en"
    target_language: str = "de"
    last_login: Optional[datetime] = None


@dataclass
class AuthSession:
    """Represents a user session"""
    session_token: str
    user: AuthUser
    expires_at: datetime
    created_at: datetime


# Note: Exception classes have been moved to core.exceptions for unified error handling.
# Import them from core.exceptions instead of defining them here.
# This eliminates duplication and provides consistent error responses across the application.
