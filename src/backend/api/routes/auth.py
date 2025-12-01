"""
Authentication API routes
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import current_active_user
from core.config.logging_config import get_logger
from core.database import get_async_session
from core.exceptions import AuthenticationError
from database.models import User
from services.authservice.refresh_token_service import RefreshTokenService
from services.authservice.token_service import TokenService

from ..models.auth import UserResponse

logger = get_logger(__name__)
router = APIRouter(tags=["authentication"])


# Note: Core authentication endpoints (register, login, logout) are handled by FastAPI-Users


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh (for non-browser clients)"""

    refresh_token: str | None = None


class TokenRefreshResponse(BaseModel):
    """Response model for token refresh with rotation"""

    access_token: str
    refresh_token: str  # New refresh token (rotated)
    token_type: str = "bearer"
    expires_in: int


@router.get("/me", response_model=UserResponse, name="auth_get_current_user")
async def get_current_user_info(current_user: Annotated[User, Depends(current_active_user)]):
    """
    Get current authenticated user information.

    This endpoint returns the profile information for the currently authenticated user.
    Requires a valid JWT access token in the Authorization header.

    **Authentication Required**: Yes

    Returns:
        UserResponse: User profile information including:
            - id: Unique user identifier (UUID)
            - username: User's username
            - email: User's email address
            - is_superuser: Whether user has admin privileges
            - is_active: Whether user account is active
            - created_at: Account creation timestamp (ISO format)
            - last_login: Last login timestamp (ISO format, nullable)

    Raises:
        HTTPException: 401 Unauthorized if token is invalid or missing

    Example:
        ```bash
        curl -H "Authorization: Bearer <token>" http://localhost:8000/api/auth/me
        ```

        Response:
        ```json
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "johndoe",
            "email": "john@example.com",
            "is_superuser": false,
            "is_active": true,
            "created_at": "2025-10-03T10:00:00",
            "last_login": "2025-10-03T11:30:00"
        }
        ```
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
    )


@router.post("/token/refresh", response_model=TokenRefreshResponse, name="auth_refresh_token")
async def refresh_access_token(
    response: Response,
    body: TokenRefreshRequest | None = None,
    refresh_token_cookie: str = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Refresh access token with automatic token rotation

    This endpoint exchanges a valid refresh token for:
    1. A new access token (for API calls)
    2. A new refresh token (rotated from old one)

    Token Sources (in order of priority):
    1. HTTP-only cookie (recommended for browsers)
    2. Request body (for non-browser clients like mobile apps)

    Token Rotation Security:
    - Each refresh token can only be used once
    - If an old token is reused, it indicates theft and all tokens are revoked
    - Rotation creates a "family" of tokens that are tracked together

    Returns:
        TokenRefreshResponse: New access token and rotated refresh token

    Raises:
        HTTPException: 401 if refresh token is invalid, expired, or reused (theft detected)

    Security Note:
        If you receive a 401 error mentioning "token reuse", all tokens have been
        revoked for security. The user must login again.
    """
    # Accept token from cookie (preferred) or body (for non-browser clients)
    refresh_token = refresh_token_cookie or (body.refresh_token if body else None)
    
    if not refresh_token:
        logger.warning("Token refresh attempted without refresh token")
        raise HTTPException(status_code=401, detail="Refresh token required")

    try:
        # Initialize refresh token service
        refresh_service = RefreshTokenService(db)

        # Rotate token (this also detects theft)
        new_refresh_token, user_id = await refresh_service.rotate_token(refresh_token)

        # Generate new access token for user
        new_access_token = TokenService.create_access_token(user_id)

        # Set new refresh token in httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="strict",
            max_age=30 * 24 * 60 * 60,  # 30 days
        )

        logger.info("Token rotated", user_id=user_id)

        return TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,  # Also return in body for clients that prefer it
            token_type="bearer",
            expires_in=TokenService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        )

    except AuthenticationError as e:
        logger.error("Token refresh failed", error=str(e))

        # Check if this was a theft detection
        if "reuse" in str(e).lower():
            logger.warning("Token theft detected - family revoked")
            detail = "Token reuse detected. All sessions revoked for security. Please login again."
        else:
            detail = "Invalid or expired refresh token. Please login again."

        raise HTTPException(status_code=401, detail=detail) from e
