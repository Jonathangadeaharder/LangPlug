"""
Authentication API models
"""
from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username must be 3-50 characters, alphanumeric with underscores and hyphens only"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long"
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Username for authentication"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Password for authentication"
    )


class UserResponse(BaseModel):
    id: UUID = Field(..., description="Unique user identifier (UUID)")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="User email address")
    is_superuser: bool = Field(..., description="Whether user has superuser privileges")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: str = Field(..., description="Account creation timestamp (ISO format)")
    last_login: str | None = Field(None, description="Last login timestamp (ISO format)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "john_doe",
                "email": "john_doe@example.com",
                "is_superuser": False,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-01-20T14:45:00Z"
            }
        }
    )


class AuthResponse(BaseModel):
    token: str = Field(..., min_length=1, description="JWT authentication token")
    user: UserResponse = Field(..., description="User information")
    expires_at: str = Field(..., description="Token expiration timestamp (ISO format)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "is_admin": False,
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z",
                    "last_login": "2024-01-20T14:45:00Z"
                },
                "expires_at": "2024-01-21T14:45:00Z"
            }
        }
    )
