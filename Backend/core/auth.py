"""FastAPI-Users authentication setup"""
import uuid
from datetime import datetime

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import EmailStr, field_validator
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.config import settings
from core.database import get_async_session


class Base(DeclarativeBase):
    pass


class User(Base):
    """FastAPI-Users compatible User model"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserCreate(BaseUserCreate):
    username: str
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(str(v).strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(str(v).strip()) == 0:
            raise ValueError('Username cannot be empty')
        return v


class UserRead(BaseUser):
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None


class UserUpdate(BaseUserUpdate):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None


class UserManager(BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    def parse_id(self, value: str) -> uuid.UUID:
        """Parse string ID to UUID."""
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {value}")

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,
        *args,
        **kwargs
    ):
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        print(f"User {user.id} logged in.")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# Cookie transport
cookie_transport = CookieTransport(
    cookie_name="langplug_auth",
    cookie_max_age=3600 * 24,  # 24 hours
    cookie_secure=False,  # Set to True in production with HTTPS
    cookie_httponly=True,
    cookie_samesite="lax",
)

# Bearer transport for JWT tokens in response body (for API use)
bearer_transport = BearerTransport(tokenUrl="auth/login")

# JWT Authentication
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=3600 * 24)

# Cookie-based authentication backend
cookie_auth_backend = AuthenticationBackend(
    name="jwt-cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# Bearer-based authentication backend (returns token in response)
bearer_auth_backend = AuthenticationBackend(
    name="jwt-bearer",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Use bearer backend for login endpoints (what tests expect)
auth_backend = bearer_auth_backend

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Current user dependencies
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_transport.scheme),
    user: User = Depends(fastapi_users.current_user(active=True, optional=True))
) -> User:
    """Get current active user with blacklist checking"""
    from .token_blacklist import token_blacklist
    from fastapi import HTTPException, status
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Handle both string tokens and HTTPAuthorizationCredentials
    if isinstance(credentials, str):
        token = credentials
    else:
        token = credentials.credentials
    
    # Check if token is blacklisted
    if await token_blacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return user

current_active_user = get_current_active_user
current_superuser = fastapi_users.current_user(active=True, superuser=True)


# JWT Authentication helper class for backward compatibility
class JWTAuthentication:
    """JWT Authentication helper for backward compatibility"""

    async def authenticate(self, token: str, db_session: AsyncSession = None) -> User | None:
        """Authenticate user by JWT token"""
        try:
            from jose import JWTError, jwt
            from .token_blacklist import token_blacklist

            # Check if token is blacklisted
            if await token_blacklist.is_blacklisted(token):
                return None

            # Decode the JWT token
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None

            # Get user from database
            if db_session is None:
                async for session in get_async_session():
                    db_session = session
                    break

            from sqlalchemy import select
            result = await db_session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user

        except (JWTError, Exception):
            return None


# Create instance for backward compatibility
jwt_authentication = JWTAuthentication()
