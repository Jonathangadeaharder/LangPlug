"""FastAPI-Users authentication setup"""

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
from pydantic import ConfigDict, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_async_session
from database.models import User


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
        import re

        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserRead(BaseUser):
    id: int
    username: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


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

    def parse_id(self, value: str) -> int:
        """Parse string ID to integer for integer-based user IDs"""
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Invalid user ID: {value}")

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
cookie_transport = CookieTransport(cookie_max_age=3600)


def get_jwt_strategy() -> JWTStrategy:
    # 24 hour token lifetime for long video processing sessions
    return JWTStrategy(secret=SECRET, lifetime_seconds=86400)


# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, int](  # Changed UUID to int
    get_user_manager,
    [auth_backend],
)

# Dependency shortcuts
current_active_user = fastapi_users.current_user(active=True)


def jwt_authentication():
    """JWT authentication for services"""
    return get_jwt_strategy
