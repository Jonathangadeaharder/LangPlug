"""Database configuration with SQLAlchemy's built-in connection pooling"""

import os
import secrets
import string
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from core.config import settings
from core.config.logging_config import get_logger

logger = get_logger(__name__)
print(f"DEBUG: Loading database.py from {__file__}", flush=True)


# Unified database base class for all models
class Base(DeclarativeBase):
    """Unified base class for all SQLAlchemy models"""

    pass


# Create async engine using configured database URL (support Postgres/SQLite)
database_url = settings.get_database_url()

engine_args = {
    "echo": settings.sqlalchemy_echo,
}

if "sqlite" in database_url:
    engine_args["poolclass"] = StaticPool
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(
    database_url,
    **engine_args,
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
            await session.commit()  # Commit changes before closing
        except Exception:
            await session.rollback()  # Rollback on error
            raise
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
    
    # Seed test data if provided
    await seed_test_data()


async def seed_test_data():
    """Seed database with test data from environment variable"""
    test_data_json = os.getenv("TEST_DATA")
    print(f"DEBUG: seed_test_data called. TEST_DATA present: {bool(test_data_json)}")
    if not test_data_json:
        print("DEBUG: TEST_DATA is empty")
        return

    import json
    from core.auth import User
    from core.auth.auth_security import SecurityConfig

    import sys
    try:
        data = json.loads(test_data_json)
        users = data.get("users", [])
        logger.info(f"DEBUG: Found {len(users)} users in TEST_DATA")
        logger.info(f"DEBUG: Users list: {[u['username'] for u in users]}")
        
        async with AsyncSessionLocal() as session:
            for user_data in users:
                try:
                    logger.info(f"DEBUG: Processing {user_data['username']}")
                    # Check if user exists
                    logger.info(f"DEBUG: Checking existence of {user_data['username']}")
                    result = await session.execute(select(User).where(User.username == user_data["username"]))
                    if not result.scalar_one_or_none():
                        logger.info(f"DEBUG: Creating user {user_data['username']}")
                        
                        logger.info("DEBUG: Calling hash_password...")
                        hashed_password = SecurityConfig.hash_password(user_data["password"])
                        logger.info("DEBUG: hash_password done.")
                        
                        logger.info("DEBUG: Instantiating User...")
                        user = User(
                            # Let DB generate ID to avoid conflicts
                            # id=user_data.get("id"),
                            email=user_data["email"],
                            username=user_data["username"],
                            hashed_password=hashed_password,
                            is_active=True,
                            is_superuser=user_data.get("role") == "admin",
                            is_verified=True,
                        )
                        logger.info("DEBUG: User instantiated.")
                        
                        logger.info("DEBUG: Adding user to session...")
                        session.add(user)
                        logger.info("DEBUG: User added to session.")
                        
                        logger.info(f"DEBUG: Added user {user_data['username']} to session. Flushing...")
                        await session.flush()
                        logger.info(f"DEBUG: Flushed user {user_data['username']}")
                    else:
                        logger.info(f"DEBUG: User {user_data['username']} already exists")
                except Exception as loop_error:
                    logger.error(f"DEBUG: Error processing user {user_data['username']}: {loop_error}")
                    import traceback
                    traceback.print_exc()
                    raise
            logger.info("DEBUG: Committing session...")
            await session.commit()
            logger.info(f"Seeded {len(users)} users from TEST_DATA")
            logger.info(f"DEBUG: Seeding complete")
            
    except Exception as e:
        logger.error(f"Failed to seed test data: {e}")
        logger.error(f"DEBUG: Seeding failed: {e}")
        import traceback
        traceback.print_exc()


async def create_default_admin_user():
    """Create default admin user with secure credentials from environment"""
    # Import here to avoid circular imports - these modules depend on Base
    from core.auth import User
    from core.auth.auth_security import SecurityConfig

    async with AsyncSessionLocal() as session:
        # Check if admin user already exists
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            # Get admin password from environment, with fallback to a secure default
            admin_password = os.getenv("LANGPLUG_ADMIN_PASSWORD")

            if not admin_password:
                logger.warning(
                    "LANGPLUG_ADMIN_PASSWORD environment variable not set. "
                    "Please set a strong password for the admin account. "
                    "Using a temporary secure password for this session."
                )
                # Generate a temporary secure password
                chars = string.ascii_letters + string.digits + string.punctuation
                admin_password = "".join(secrets.choice(chars) for _ in range(24))
                logger.info("Temporary admin password generated - check logs securely")

            # Create admin user with password from environment or generated
            hashed_password = SecurityConfig.hash_password(admin_password)
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
            logger.info(
                "Default admin user created (username: admin, email: admin@langplug.com). "
                "Password from LANGPLUG_ADMIN_PASSWORD environment variable."
            )


async def close_db():
    """Close database connections"""
    await engine.dispose()
