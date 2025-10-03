"""
Authentication Service

Core authentication service for LangPlug providing user registration, login, and session management.
This module handles secure password hashing, session lifecycle, and user credential validation.

Key Components:
    - AuthService: Main authentication service class
    - Password validation via PasswordValidator
    - In-memory session storage with database persistence
    - Argon2 password hashing for security

Usage Example:
    ```python
    from services.authservice.auth_service import AuthService
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession() as db:
        auth_service = AuthService(db)
        user = await auth_service.register_user("username", "SecurePass123!")
        session = await auth_service.login("username", "SecurePass123!")
        validated_user = await auth_service.validate_session(session.session_token)
    ```

Dependencies:
    - sqlalchemy: Database operations
    - secrets: Cryptographically secure token generation
    - core.transaction: Transaction boundary management
    - database.models: User model
    - .password_validator: Password strength validation and hashing

Thread Safety:
    No. AuthService uses instance-level session storage (_sessions dict) which is not thread-safe.
    Each request should use a separate service instance with its own database session.

Performance Notes:
    - In-memory session storage provides O(1) lookup
    - Password hashing is intentionally slow (Argon2) for security
    - Database operations are async for non-blocking I/O
"""

import secrets
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Import exceptions from core.exceptions (unified error handling)
from core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    SessionExpiredError,
    UserAlreadyExistsError,
)
from core.transaction import transactional
from database.models import User

# Import data models from local models module
from .models import AuthSession, AuthUser
from .password_validator import PasswordValidator


class AuthService:
    """
    Authentication service with secure Argon2 password hashing and session management.

    Provides user registration, login, session validation, and logout functionality.
    Sessions are stored in-memory for fast access, with user data persisted in database.

    Attributes:
        db_session (AsyncSession): Database session for user operations
        session_lifetime_hours (int): Session expiration time in hours (default: 24)
        _sessions (dict): In-memory session storage, keyed by session_token

    Example:
        ```python
        async with get_db_session() as db:
            auth_service = AuthService(db)

            # Register new user
            user = await auth_service.register_user("alice", "SecurePass123!")

            # Login
            session = await auth_service.login("alice", "SecurePass123!")

            # Validate session
            user = await auth_service.validate_session(session.session_token)

            # Logout
            await auth_service.logout(session.session_token)
        ```

    Note:
        Sessions are lost on server restart since they're in-memory.
        For production, consider Redis or database-backed session storage.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # Set default session lifetime
        self.session_lifetime_hours = 24
        # In-memory session storage
        self._sessions = {}

    def _hash_password(self, password: str) -> str:
        """
        Hash password using Argon2 algorithm.

        This method delegates to PasswordValidator for consistent hashing across the application.

        Args:
            password (str): Plain text password to hash

        Returns:
            str: Argon2 hashed password string

        Note:
            Argon2 is memory-hard and resistant to GPU/ASIC attacks.
            Hashing is intentionally slow (~0.5s) for security.
        """
        return PasswordValidator.hash_password(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against Argon2 hash.

        Args:
            plain_password (str): Plain text password to verify
            hashed_password (str): Stored Argon2 hash to compare against

        Returns:
            bool: True if password matches, False otherwise

        Note:
            Timing-safe comparison prevents timing attacks.
        """
        return PasswordValidator.verify_password(plain_password, hashed_password)

    @transactional
    async def register_user(self, username: str, password: str) -> User:
        """
        Register a new user with validated credentials.

        Creates a new user account with Argon2 hashed password. Transaction boundaries
        ensure atomic creation - either user is fully created or no changes persist.

        Args:
            username (str): Username for new account (min 3 characters)
            password (str): Plain text password (must meet strength requirements)

        Returns:
            User: Newly created user database model

        Raises:
            ValueError: If username too short or password fails strength validation
            UserAlreadyExistsError: If username already exists in database
            AuthenticationError: If user creation fails for other reasons

        Example:
            ```python
            try:
                user = await auth_service.register_user("alice", "SecurePass123!")
                print(f"User {user.username} created with ID {user.id}")
            except ValueError as e:
                print(f"Invalid input: {e}")
            except UserAlreadyExistsError:
                print("Username already taken")
            ```

        Note:
            Password validation requires: 12+ chars, uppercase, lowercase, digit, special char.
            Email is auto-generated as {username}@example.com.
        """
        # Validate username
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        # Validate password strength
        is_valid, error_msg = PasswordValidator.validate(password)
        if not is_valid:
            raise ValueError(error_msg)

        # Check if user exists
        stmt = select(User).where(User.username == username)
        result = await self.db_session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise UserAlreadyExistsError(f"User '{username}' already exists")

        # Create user with hashed password (Argon2)
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
            await self.db_session.flush()  # Flush within transaction, commit handled by decorator
            await self.db_session.refresh(new_user)

            return new_user

        except Exception as e:
            # Transaction will auto-rollback on exception
            raise AuthenticationError(f"Failed to register user: {e}") from e

    @transactional
    async def login(self, username: str, password: str) -> AuthSession:
        """
        Authenticate user and create a new session.

        Validates credentials, creates a cryptographically secure session token,
        and updates the user's last_login timestamp. Session stored in-memory for fast access.

        Args:
            username (str): Username to authenticate
            password (str): Plain text password to verify

        Returns:
            AuthSession: Session object containing token, user info, and expiration

        Raises:
            InvalidCredentialsError: If username not found or password incorrect
            AuthenticationError: If session creation or database update fails

        Example:
            ```python
            try:
                session = await auth_service.login("alice", "SecurePass123!")
                print(f"Session token: {session.session_token}")
                print(f"Expires at: {session.expires_at}")
            except InvalidCredentialsError:
                print("Invalid username or password")
            ```

        Note:
            Session lifetime is 24 hours by default.
            Token is URL-safe base64 encoded (32 bytes = 43 chars).
            Password verification uses constant-time comparison.
        """
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
            await self.db_session.flush()  # Flush within transaction, commit handled by decorator
        except Exception as e:
            # Transaction will auto-rollback on exception
            raise AuthenticationError(f"Failed to create session: {e}") from e

        return new_session

    async def validate_session(self, session_token: str) -> User:
        """
        Validate session token and retrieve authenticated user.

        Checks session existence, expiration, and user validity. Automatically cleans up
        expired or invalid sessions.

        Args:
            session_token (str): Session token to validate (43-char URL-safe base64)

        Returns:
            User: Authenticated user database model

        Raises:
            SessionExpiredError: If session not found, expired, or user deleted
            AuthenticationError: If validation fails for other reasons

        Example:
            ```python
            try:
                user = await auth_service.validate_session(token)
                print(f"Authenticated as: {user.username}")
            except SessionExpiredError:
                print("Session expired, please login again")
            ```

        Note:
            Expired sessions are automatically removed from in-memory storage.
            This is NOT transactional - only reads from database.
        """
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
            raise AuthenticationError(f"Failed to validate session: {e}") from e

    async def logout(self, session_token: str) -> bool:
        """
        Logout user by removing their session.

        Removes session from in-memory storage, effectively invalidating the token.

        Args:
            session_token (str): Session token to invalidate

        Returns:
            bool: True if session was found and removed, False if not found

        Raises:
            AuthenticationError: If logout operation fails

        Example:
            ```python
            success = await auth_service.logout(session_token)
            if success:
                print("Logged out successfully")
            else:
                print("Session not found (already logged out?)")
            ```

        Note:
            This is NOT transactional - only modifies in-memory state.
            Safe to call multiple times with same token (idempotent).
        """
        try:
            # Remove session from memory
            removed = self._sessions.pop(session_token, None)
            return removed is not None
        except Exception as e:
            raise AuthenticationError(f"Failed to logout: {e}") from e

    async def update_language_preferences(self, user_id: int, native_language: str, target_language: str) -> bool:
        """
        Update user's language learning preferences.

        NOTE: This is currently a no-op placeholder. Language preferences need to be added
        to the User model before this method can be fully implemented.

        Args:
            user_id (int): User ID to update
            native_language (str): User's native language code (e.g., 'en', 'es')
            target_language (str): Language user is learning (e.g., 'de', 'fr')

        Returns:
            bool: Always returns True (placeholder)

        Raises:
            AuthenticationError: If update operation fails

        Example:
            ```python
            success = await auth_service.update_language_preferences(
                user_id=1,
                native_language="en",
                target_language="de"
            )
            ```

        Note:
            TODO: Add native_language and target_language columns to User model.
            Currently returns True without persisting any changes.
        """
        try:
            # Note: Language preferences would need to be added to User model
            # For now, this is a no-op since we don't have language preference fields
            # in the FastAPI-Users User model yet
            return True
        except Exception as e:
            await self.db_session.rollback()
            raise AuthenticationError(f"Failed to update language preferences: {e}") from e

    def cleanup(self):
        """
        Cleanup service resources.

        Closes database session and clears all in-memory sessions. Should be called
        when service instance is no longer needed.

        Note:
            This will invalidate all active sessions. Only call during shutdown or
            when completely replacing the service instance.
        """
        if hasattr(self.db_session, "close"):
            self.db_session.close()
        self._sessions.clear()
