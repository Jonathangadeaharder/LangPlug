"""
Authentication domain models and DTOs
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    """User creation request"""

    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login request"""

    username: str
    password: str


class UserResponse(BaseModel):
    """User response model"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: datetime | None = None


class TokenResponse(BaseModel):
    """Authentication token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordUpdate(BaseModel):
    """Password update request"""

    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    """Password reset request"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""

    token: str
    new_password: str
