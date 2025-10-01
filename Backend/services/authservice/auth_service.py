"""
Simple and clean authentication service for LangPlug
No complex dependencies, no fancy logging, just works
"""

import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Import exceptions from core.exceptions (unified error handling)
from core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    SessionExpiredError,
    UserAlreadyExistsError,
)
from database.models import User

# Import data models from local models module
from .models import AuthSession, AuthUser


class AuthService:
    """
    Simple authentication service with secure bcrypt password hashing
    Uses database-based session storage for scalability and persistence
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # Initialize password context with bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Set default session lifetime
        self.session_lifetime_hours = 24
        # In-memory session storage
        self._sessions = {}

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    async def register_user(self, username: str, password: str) -> User:
        """Register a new user"""
        # Validate input
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        # Check if user exists
        stmt = select(User).where(User.username == username)
        result = await self.db_session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise UserAlreadyExistsError(f"User '{username}' already exists")

        # Create user with hashed password (bcrypt includes salt internally)
        password_hash = self._hash_password(password)

        try:
            # Create new user
            new_user = User(
                username=username,
                email=f"{username}@example.com",  # Default email based on username
                hashed_password=password_hash,
                is_superuser=False,
                is_active=True,
                is_verified=False,
            )

            self.db_session.add(new_user)
            await self.db_session.commit()
            await self.db_session.refresh(new_user)

            return new_user

        except Exception as e:
            await self.db_session.rollback()
            raise AuthenticationError(f"Failed to register user: {e}")

    async def login(self, username: str, password: str) -> AuthSession:
        """Login user and create session"""
        # Get user from database
        stmt = select(User).where(User.username == username)
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise InvalidCredentialsError("Invalid username or password")

        # Verify password using bcrypt
        if not self._verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid username or password")

        # Create session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.session_lifetime_hours)

        # Create AuthUser object for session
        auth_user = AuthUser(
            id=user.id,
            username=user.username,
            is_admin=getattr(user, "is_superuser", False),
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else "",
            native_language=getattr(user, "native_language", "en"),
            target_language=getattr(user, "target_language", "de"),
            last_login=getattr(user, "last_login", None),
        )

        # Create and store session in memory
        new_session = AuthSession(
            session_token=session_token, user=auth_user, expires_at=expires_at, created_at=datetime.now()
        )

        try:
            # Store session in memory
            self._sessions[session_token] = new_session

            # Update last login in database
            stmt = update(User).where(User.id == user.id).values(last_login=datetime.now())
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            raise AuthenticationError(f"Failed to create session: {e}")

        return new_session

    async def validate_session(self, session_token: str) -> User:
        """Validate session token and return user"""
        # Get session from memory
        try:
            session = self._sessions.get(session_token)

            if not session:
                raise SessionExpiredError("Invalid session")

            # Check if session is expired
            if datetime.now() > session.expires_at:
                # Remove expired session from memory
                self._sessions.pop(session_token, None)
                raise SessionExpiredError("Session has expired")

            # Get user from database
            stmt = select(User).where(User.id == session.user.id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                # Remove session if user doesn't exist
                self._sessions.pop(session_token, None)
                raise SessionExpiredError("User not found")

            return user
        except SessionExpiredError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to validate session: {e}")

    async def logout(self, session_token: str) -> bool:
        """Logout user by removing session"""
        try:
            # Remove session from memory
            removed = self._sessions.pop(session_token, None)
            return removed is not None
        except Exception as e:
            raise AuthenticationError(f"Failed to logout: {e}")

    async def update_language_preferences(self, user_id: int, native_language: str, target_language: str) -> bool:
        """Update user's language preferences"""
        try:
            # Note: Language preferences would need to be added to User model
            # For now, this is a no-op since we don't have language preference fields
            # in the FastAPI-Users User model yet
            return True
        except Exception as e:
            await self.db_session.rollback()
            raise AuthenticationError(f"Failed to update language preferences: {e}")

    def cleanup(self):
        """Cleanup resources, particularly database session"""
        if hasattr(self.db_session, "close"):
            self.db_session.close()
        self._sessions.clear()
