"""
Authentication service interfaces providing clean contracts for auth operations.
"""

from abc import abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

from .base import IAsyncService


class IAuthService(IAsyncService):
    """Interface for authentication operations"""

    @abstractmethod
    async def authenticate_user(self, username: str, password: str, db: AsyncSession) -> User | None:
        """Authenticate user with username and password"""
        pass

    @abstractmethod
    async def create_user(
        self, username: str, password: str, email: str | None = None, db: AsyncSession = None
    ) -> User:
        """Create a new user account"""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> User | None:
        """Get user by ID"""
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str, db: AsyncSession) -> User | None:
        """Get user by username"""
        pass

    @abstractmethod
    async def update_user(self, user_id: int, updates: dict[str, Any], db: AsyncSession) -> User:
        """Update user information"""
        pass

    @abstractmethod
    async def change_password(self, user_id: int, old_password: str, new_password: str, db: AsyncSession) -> bool:
        """Change user password"""
        pass

    @abstractmethod
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        pass

    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Hash a password"""
        pass


class ITokenService(IAsyncService):
    """Interface for token management operations"""

    @abstractmethod
    async def create_access_token(self, user_id: int, expires_minutes: int | None = None) -> str:
        """Create access token for user"""
        pass

    @abstractmethod
    async def create_refresh_token(self, user_id: int, expires_days: int | None = None) -> str:
        """Create refresh token for user"""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify and decode token"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke/blacklist a token"""
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> str | None:
        """Create new access token from refresh token"""
        pass


class IPermissionService(IAsyncService):
    """Interface for permission and authorization operations"""

    @abstractmethod
    async def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for action on resource"""
        pass

    @abstractmethod
    async def grant_permission(self, user_id: int, resource: str, action: str, db: AsyncSession) -> bool:
        """Grant permission to user"""
        pass

    @abstractmethod
    async def revoke_permission(self, user_id: int, resource: str, action: str, db: AsyncSession) -> bool:
        """Revoke permission from user"""
        pass

    @abstractmethod
    async def get_user_permissions(self, user_id: int, db: AsyncSession) -> list[dict[str, str]]:
        """Get all permissions for user"""
        pass
