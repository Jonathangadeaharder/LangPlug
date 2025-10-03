"""Database configuration with SQLAlchemy's built-in connection pooling"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from core.config import settings

logger = logging.getLogger(__name__)


# Unified database base class for all models
class Base(DeclarativeBase):
    """Unified base class for all SQLAlchemy models"""

    pass


# Create async engine with built-in connection pooling
if settings.db_type == "postgresql":
    # PostgreSQL with asyncpg
    database_url = settings.get_database_url().replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        database_url,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
        pool_pre_ping=True,
        echo=settings.sqlalchemy_echo,
    )
else:
    # SQLite with aiosqlite
    database_url = f"sqlite+aiosqlite:///{settings.get_database_path()}"
    engine = create_async_engine(
        database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.sqlalchemy_echo,
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_and_tables():
    """Create database tables"""
    # Import all models to ensure they're registered with Base
    import database.models  # noqa: F401 - Import all models
    from core.auth import User  # noqa: F401 - Import User model

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_db():
    """Initialize database tables and create default admin user"""
    # Import all models to ensure they're registered with Base
    import database.models  # noqa: F401 - Import all models
    from core.auth import User  # noqa: F401 - Import User model

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create default admin user if it doesn't exist
    await create_default_admin_user()


async def create_default_admin_user():
    """Create default admin user with secure credentials"""
    from passlib.context import CryptContext
    from sqlalchemy import select

    from core.auth import User

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with AsyncSessionLocal() as session:
        # Check if admin user already exists
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            # Create admin user with secure password meeting validation requirements
            # Password: AdminPass123! (12+ chars, upper, lower, digit, special)
            hashed_password = pwd_context.hash("AdminPass123!")
            admin_user = User(
                email="admin@langplug.com",
                username="admin",
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
            session.add(admin_user)
            await session.commit()
            logger.info("Default admin user created (username: admin, email: admin@langplug.com, password: AdminPass123!)")


async def close_db():
    """Close database connections"""
    await engine.dispose()
