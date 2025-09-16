"""
Authentication API routes
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated

from ..models.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from core.dependencies import current_active_user
from core.auth import auth_backend, fastapi_users
from database.models import User
from core.auth import UserCreate, UserRead

logger = logging.getLogger(__name__)
router = APIRouter(tags=["authentication"])

@router.get("/test-prefix", name="auth_test_prefix")
async def test_prefix_endpoint():
    """Test endpoint to verify router prefix configuration"""
    return {"message": "Auth router is working", "prefix": "should be /auth", "timestamp": "2025-01-14"}


# All authentication endpoints are now handled by FastAPI-Users
# Register: POST /auth/register
# Login: POST /auth/login  
# Logout: POST /auth/logout


@router.get("/me", response_model=UserResponse, name="auth_get_current_user")
async def get_current_user_info(
    current_user: Annotated[User, Depends(current_active_user)]
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )