"""
Authentication API models
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: "UserResponse"
    expires_at: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool
    created_at: str
    last_login: Optional[str] = None