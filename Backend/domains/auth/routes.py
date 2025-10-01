"""
Authentication domain routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from core.database_session import get_db
from core.exceptions import AuthenticationError, ValidationError
from core.service_container import get_auth_service

from .models import PasswordUpdate, TokenResponse, UserCreate, UserLogin, UserResponse
from .services import AuthenticationService

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Register a new user"""
    try:
        return await auth_service.register_user(db, user_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Authenticate user and return token"""
    try:
        return await auth_service.login_user(db, login_data)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service),
    token: str = Depends(security),
):
    """Get current user information"""
    try:
        user = await auth_service.get_current_user(db, token.credentials)
        return UserResponse.from_orm(user)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"}
        )


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service),
    token: str = Depends(security),
):
    """Update user password"""
    try:
        user = await auth_service.get_current_user(db, token.credentials)
        await auth_service.update_password(db, user.id, password_data.current_password, password_data.new_password)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password update failed")
