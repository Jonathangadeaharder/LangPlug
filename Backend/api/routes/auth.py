"""
Authentication API routes
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..models.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from core.dependencies import get_auth_service, get_current_user, security

logger = logging.getLogger(__name__)
router = APIRouter(tags=["authentication"])


@router.post("/auth/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    auth_service = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        logger.info(f"User registration attempt for username: {request.username}")
        user = auth_service.register_user(request.username, request.password)
        logger.info(f"User registered successfully: {user.username}")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except Exception as e:
        if "already exists" in str(e):
            logger.warning(f"Registration failed - user exists: {request.username}")
            raise HTTPException(status_code=400, detail=str(e))
        elif "must be at least" in str(e):
            logger.warning(f"Registration failed - validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        else:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/auth/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service = Depends(get_auth_service)
):
    """Login user and create session"""
    try:
        logger.info(f"Login attempt for username: {request.username}")
        session = auth_service.login(request.username, request.password)
        logger.info(f"User logged in successfully: {request.username}")
        
        return AuthResponse(
            token=session.session_token,
            user=UserResponse(
                id=session.user.id,
                username=session.user.username,
                is_admin=session.user.is_admin,
                is_active=session.user.is_active,
                created_at=session.user.created_at,
                last_login=session.user.last_login
            ),
            expires_at=session.expires_at.isoformat()
        )
    except Exception as e:
        if "Invalid username or password" in str(e):
            logger.warning(f"Login failed for username: {request.username}")
            raise HTTPException(status_code=401, detail=str(e))
        else:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=500, detail="Login failed")


@router.post("/auth/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service = Depends(get_auth_service)
):
    """Logout current user"""
    token = credentials.credentials
    success = auth_service.logout(token)
    logger.info(f"User logged out, success: {success}")
    return {"success": success}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )