"""User repository for database operations - Synchronous version"""

from datetime import datetime

from sqlalchemy.orm import Session

from database.models import User
from database.repositories.base_repository_sync import BaseSyncRepository
from database.repositories.interfaces import UserRepositoryInterface


class UserRepositorySync(BaseSyncRepository[User, int], UserRepositoryInterface):
    """Repository for User entity operations"""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: Session, email: str) -> User | None:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()

    async def get_by_username(self, db: Session, username: str) -> User | None:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    async def update_last_login(self, db: Session, user_id: int) -> bool:
        """Update user's last login timestamp"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
            return True
        return False

    async def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all active users"""
        return db.query(User).filter(User.is_active).offset(skip).limit(limit).all()

    async def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Deactivate a user account"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.is_active = False
            db.commit()
            return True
        return False

    async def update_password(self, db: Session, user_id: int, hashed_password: str) -> bool:
        """Update user's password"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.hashed_password = hashed_password
            db.commit()
            return True
        return False

    async def verify_user(self, db: Session, user_id: int) -> bool:
        """Mark user as verified"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.is_verified = True
            db.commit()
            return True
        return False
