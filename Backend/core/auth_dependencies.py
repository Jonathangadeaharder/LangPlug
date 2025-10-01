"""Authentication dependencies for FastAPI"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

from .auth import current_active_user
from .database import get_async_session as get_db_session
from .logging_config import get_logger

security = HTTPBearer()
logger = get_logger(__name__)


async def get_current_user_ws(token: str, db: Annotated[AsyncSession, Depends(get_db_session)]) -> User:
    """Validate session token for WebSocket connections with blacklist check"""
    from .auth import jwt_authentication
    from .token_blacklist import token_blacklist

    # Check if token is blacklisted
    if await token_blacklist.is_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    try:
        user = await jwt_authentication.authenticate(token, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")


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
        from .auth import jwt_authentication

        user = await jwt_authentication.authenticate(token, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")


__all__ = ["current_active_user", "get_current_user_ws", "get_optional_user", "get_user_from_query_token", "security"]
