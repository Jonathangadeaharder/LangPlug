"""Repository for user-related database operations"""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user database operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def find_by_username(self, username: str) -> User | None:
        """Find user by username"""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        stmt = update(User).where(User.id == user_id).values(last_login=datetime.utcnow())
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user's password"""
        stmt = update(User).where(User.id == user_id).values(hashed_password=hashed_password)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def verify_user(self, user_id: int) -> bool:
        """Mark user as verified"""
        stmt = update(User).where(User.id == user_id).values(is_verified=True)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        stmt = update(User).where(User.id == user_id).values(is_active=False)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def activate_user(self, user_id: int) -> bool:
        """Activate a user account"""
        stmt = update(User).where(User.id == user_id).values(is_active=True)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
