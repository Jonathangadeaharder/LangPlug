"""FastAPI-Users authentication setup with Argon2 password hashing"""

from datetime import datetime

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import ConfigDict, EmailStr, field_serializer, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_async_session
from database.models import User
from services.authservice.password_validator import PasswordValidator


class UserCreate(BaseUserCreate):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        import re

        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username must be no more than 50 characters long")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username must contain only alphanumeric characters, underscores, and hyphens")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """
        Validate password using PasswordValidator for strong security
        Requires 12 characters minimum with complexity requirements
        """

        is_valid, error_msg = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UserRead(BaseUser):
    id: int
    username: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Convert datetime to ISO format string"""
        return value.isoformat()

    @field_serializer("last_login")
    def serialize_last_login(self, value: datetime | None) -> str | None:
        """Convert datetime to ISO format string"""
        if value is None:
            return None
        return value.isoformat()


class UserUpdate(BaseUserUpdate):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None


if not settings.secret_key:
    raise ValueError("SECRET_KEY environment variable is required for production")

SECRET = settings.secret_key


class UserManager(BaseUserManager[User, int]):  # Changed UUID to int
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    # fastapi-users 14.0.1 uses pwdlib with Argon2 by default
    # No need for custom password helper

    def parse_id(self, value: str) -> int:
        """Parse string ID to integer for integer-based user IDs"""
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(f"Invalid user ID: {value}") from e

    async def on_after_register(self, user: User, request: Request | None = None):
        pass

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None):
        pass

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None):
        pass


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# Setup transports and strategy
bearer_transport = BearerTransport(tokenUrl="auth/login")

# Configure secure cookie transport
# HttpOnly is True by default in CookieTransport
# Secure should be True in production (HTTPS)
cookie_transport = CookieTransport(
    cookie_max_age=settings.jwt_access_token_expire_minutes * 60,
    cookie_name="fastapiusersauth",
    cookie_secure=settings.environment == "production",
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy:
    # 1 hour token lifetime (reduced from 24h for security)
    # Use refresh tokens for longer sessions
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


# Authentication backend (Legacy Bearer)
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Authentication backend (Secure Cookie)
cookie_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, int](  # Changed UUID to int
    get_user_manager,
    [auth_backend, cookie_auth_backend],
)

# Dependency shortcuts
current_active_user = fastapi_users.current_user(active=True)


class JWTAuthentication:
    """JWT authentication helper for manual token validation"""

    @staticmethod
    async def authenticate(token: str, db: AsyncSession) -> User | None:
        """
        Authenticate a JWT token and return the user

        Args:
            token: JWT token string
            db: Database session

        Returns:
            User object if valid, None otherwise
        """
        try:
            strategy = get_jwt_strategy()
            user_db = SQLAlchemyUserDatabase(db, User)
            user_manager = UserManager(user_db)

            # Use strategy to decode and validate token
            user = await strategy.read_token(token, user_manager=user_manager)
            return user
        except Exception:
            return None


# Create singleton instance for backwards compatibility
jwt_authentication = JWTAuthentication()
