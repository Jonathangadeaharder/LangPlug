"""Authentication dependencies for FastAPI with proper DI"""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger
from core.database.database import get_async_session as get_db_session
from database.models import User

from .auth import current_active_user

if TYPE_CHECKING:
    from .token_blacklist import TokenBlacklist

security = HTTPBearer()
logger = get_logger(__name__)

# Singleton instances managed at application level
_token_blacklist_instance = None
_login_tracker_instance = None


def get_token_blacklist():
    """
    Get TokenBlacklist singleton instance

    Returns:
        TokenBlacklist: Singleton instance for token revocation

    Raises:
        RuntimeError: If TokenBlacklist not initialized (call init_auth_services on startup)
    """
    global _token_blacklist_instance
    if _token_blacklist_instance is None:
        raise RuntimeError("TokenBlacklist not initialized. Call init_auth_services() on startup")
    return _token_blacklist_instance


def get_login_tracker():
    """
    Get LoginAttemptTracker singleton instance

    Returns:
        LoginAttemptTracker: Singleton instance for rate limiting

    Raises:
        RuntimeError: If LoginAttemptTracker not initialized (call init_auth_services on startup)
    """
    global _login_tracker_instance
    if _login_tracker_instance is None:
        raise RuntimeError("LoginAttemptTracker not initialized. Call init_auth_services() on startup")
    return _login_tracker_instance


def init_auth_services():
    """
    Initialize authentication services (call on app startup)

    Creates singleton instances of:
    - TokenBlacklist (in-memory)
    - LoginAttemptTracker
    """
    from .auth_security import LoginAttemptTracker
    from .token_blacklist import TokenBlacklist

    global _token_blacklist_instance, _login_tracker_instance

    # Initialize TokenBlacklist (in-memory)
    _token_blacklist_instance = TokenBlacklist()

    # Initialize LoginAttemptTracker
    _login_tracker_instance = LoginAttemptTracker()

    logger.info("Authentication services initialized (TokenBlacklist, LoginTracker - in-memory)")


def cleanup_auth_services():
    """
    Cleanup authentication services (call on app shutdown)

    Clears singleton instances to free resources.
    """
    global _token_blacklist_instance, _login_tracker_instance
    _token_blacklist_instance = None
    _login_tracker_instance = None
    logger.info("Authentication services cleaned up")


async def get_current_user_ws(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    blacklist: Annotated["TokenBlacklist", Depends(get_token_blacklist)],
) -> User:
    """Validate session token for WebSocket connections with blacklist check"""
    from .auth import jwt_authentication

    # Check if token is blacklisted
    if await blacklist.is_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        user = await jwt_authentication.authenticate(token, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication") from e


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> User | None:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None

    try:
        from .auth import jwt_authentication

        token = credentials.credentials
        user = await jwt_authentication.authenticate(token, db)
        return user
    except Exception:
        return None


async def get_user_from_query_token(
    token: str | None = Query(None, description="Authentication token"),
    authorization: str | None = Header(None, description="Bearer access token"),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> User:
    """Authenticate user via query parameter token (for video streaming)"""
    if not token and authorization:
        auth_value = authorization.strip()
        if auth_value.lower().startswith("bearer "):
            token = auth_value[7:].strip()
        elif auth_value:
            token = auth_value

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required")

    try:
        from fastapi_users.db import SQLAlchemyUserDatabase

        from .auth import auth_backend, get_user_db, get_user_manager

        # Get JWT strategy from auth backend
        strategy = auth_backend.get_strategy()

        # Get user database and user manager
        user_db_gen = get_user_db(db)
        user_db: SQLAlchemyUserDatabase = await anext(user_db_gen)

        try:
            user_manager_gen = get_user_manager(user_db)
            user_manager = await anext(user_manager_gen)

            try:
                # Decode and validate the token - returns User object, not ID
                user = await strategy.read_token(token, user_manager=user_manager)
                if user is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

                # Check if user is active
                if not user.is_active:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")

                return user
            finally:
                # Close the user manager generator
                await user_manager_gen.aclose()
        finally:
            # Close the user db generator
            await user_db_gen.aclose()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token authentication failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from e


__all__ = [
    "cleanup_auth_services",
    "current_active_user",
    "get_current_user_ws",
    "get_login_tracker",
    "get_optional_user",
    "get_token_blacklist",
    "get_user_from_query_token",
    "init_auth_services",
    "security",
]
