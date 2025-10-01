"""
Repository Package
Standardized database access patterns for all services
"""

from .base_repository import BaseRepository
from .user_repository import User, UserRepository

__all__ = ["BaseRepository", "User", "UserRepository"]
