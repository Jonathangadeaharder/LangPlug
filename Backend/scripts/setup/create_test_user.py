import asyncio
import contextlib

from core.auth import UserCreate, get_user_db, get_user_manager
from core.database import get_async_session


async def create_user():
    async for session in get_async_session():
        user_db = await get_user_db(session).__anext__()
        user_manager = await get_user_manager(user_db).__anext__()
        user_create = UserCreate(username="logouttest", email="logouttest@example.com", password="SecurePass123")
        with contextlib.suppress(Exception):
            await user_manager.create(user_create)
        break


if __name__ == "__main__":
    asyncio.run(create_user())
