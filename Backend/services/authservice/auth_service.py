"""
Simple and clean authentication service for LangPlug
No complex dependencies, no fancy logging, just works
"""

import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserSession

from .models import (
    AuthenticationError,
    AuthSession,
    AuthUser,
    InvalidCredentialsError,
    SessionExpiredError,
    UserAlreadyExistsError,
)


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
                is_verified=False
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

        # Store session in database
        try:
            new_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                expires_at=expires_at,
                created_at=datetime.now(),
                last_used=datetime.now(),
                is_active=True
            )
            self.db_session.add(new_session)

            # Update last login
            stmt = update(User).where(User.id == user.id).values(
                last_login=datetime.now()
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            raise AuthenticationError(f"Failed to create session: {e}")

        # Create AuthUser object for session
        auth_user = AuthUser(
            id=user.id,
            username=user.username,
            is_admin=getattr(user, 'is_superuser', False),
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else '',
            native_language=getattr(user, 'native_language', 'en'),
            target_language=getattr(user, 'target_language', 'de'),
            last_login=getattr(user, 'last_login', None)
        )

        return AuthSession(
            session_token=session_token,
            user=auth_user,
            expires_at=expires_at,
            created_at=datetime.now()
        )

    async def validate_session(self, session_token: str) -> User:
        """Validate session token and return user"""
        # Get session from database with user data
        try:
            stmt = select(UserSession, User).join(User).where(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            )
            result = await self.db_session.execute(stmt)
            session_user_data = result.first()

            if not session_user_data:
                raise SessionExpiredError("Invalid or expired session")

            session, user = session_user_data

            # Check if session is expired
            if datetime.now() > session.expires_at:
                # Mark session as inactive
                stmt = update(UserSession).where(
                    UserSession.session_token == session_token
                ).values(is_active=False)
                await self.db_session.execute(stmt)
                await self.db_session.commit()
                raise SessionExpiredError("Session has expired")

            # Update last used timestamp
            stmt = update(UserSession).where(
                UserSession.session_token == session_token
            ).values(last_used=datetime.now())
            await self.db_session.execute(stmt)
            await self.db_session.commit()

            return user
        except SessionExpiredError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to validate session: {e}")

    async def logout(self, session_token: str) -> bool:
        """Logout user by deactivating session"""
        try:
            # Deactivate session
            stmt = update(UserSession).where(
                UserSession.session_token == session_token
            ).values(is_active=False)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
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