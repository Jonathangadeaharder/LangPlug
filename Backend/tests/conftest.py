"""
Modern pytest configuration with proper test database isolation and fixtures.
Follows FastAPI and SQLAlchemy best practices for testing.
"""
import pytest
import asyncio
import uuid
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path for imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.app import create_app
from core.database import get_async_session
from core.auth import User, Base, get_user_db, get_user_manager
from database.models import Base as ModelsBase
from tests.utils.url_builder import get_url_builder


# Test database setup - use in-memory SQLite for speed and isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_engine():
    """Create async database engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ModelsBase.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Each test gets a fresh database state via transaction rollback."""
    async with async_engine.connect() as connection:
        # Begin a transaction
        transaction = await connection.begin()
        
        # Create a session bound to this transaction
        async_session_maker = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = async_session_maker()

        try:
            yield session
        finally:
            # Roll back the transaction after the test is done
            await session.close()
            await transaction.rollback()


@pytest.fixture
def test_app(db_session):
    """Create FastAPI app with test database session override."""
    app = create_app()

    # Override database dependency
    async def get_test_db():
        yield db_session

    app.dependency_overrides[get_async_session] = get_test_db

    yield app

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def url_builder(test_app):
    """Create URL builder for generating robust test URLs."""
    return get_url_builder(test_app)


@pytest.fixture
def client(test_app) -> Generator[TestClient, None, None]:
    """Create test client with proper app setup."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        # Add app reference for url_path_for compatibility
        ac.app = test_app
        yield ac


@pytest.fixture
async def test_user(db_session):
    """Create a test user for authentication tests."""
    from core.auth import UserCreate
    from fastapi_users.db import SQLAlchemyUserDatabase
    from core.auth import UserManager

    # Create user database and manager
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)

    # Create user data
    user_create = UserCreate(
        email="testuser@example.com",
        username="testuser",
        password="testpassword123",
        is_superuser=False,
        is_verified=True
    )

    # Create user
    user = await user_manager.create(user_create)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def authenticated_user(test_user, test_app):
    """Create authenticated user with valid JWT token."""
    from core.auth import auth_backend

    # Create token for user
    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(test_user)

    return {
        "user": test_user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def auth_headers(authenticated_user):
    """Get authentication headers for requests."""
    return authenticated_user["headers"]


# Helper fixtures for different test types
@pytest.fixture
def unique_user_data():
    """Generate unique user data for tests."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def mock_external_service():
    """Mock external services that shouldn't be called during tests."""
    mock_service = Mock()
    mock_service.transcribe = AsyncMock(return_value="Mock transcription")
    mock_service.translate = AsyncMock(return_value="Mock translation")
    return mock_service


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "slow: Slow tests")


# Pytest collection modifications
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests based on path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)

        # Mark auth tests
        if "auth" in str(item.fspath) or "auth" in item.name:
            item.add_marker(pytest.mark.auth)


# Session-scoped fixtures for expensive operations
@pytest.fixture(scope="session")
def test_settings():
    """Test-specific settings."""
    return {
        "database_url": TEST_DATABASE_URL,
        "secret_key": "test-secret-key-for-jwt",
        "debug": True,
        "testing": True
    }


# Database testing utilities
class DatabaseTestUtils:
    """Utility methods for database testing."""

    @staticmethod
    async def create_test_user(session: AsyncSession, **kwargs):
        """Create a test user with custom parameters."""
        from core.auth import UserCreate
        from fastapi_users.db import SQLAlchemyUserDatabase
        from core.auth import UserManager

        defaults = {
            "email": f"user_{uuid.uuid4().hex[:8]}@test.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "TestPass123!",
            "is_verified": True,
            "is_active": True
        }
        defaults.update(kwargs)

        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)
        user_create = UserCreate(**defaults)

        user = await user_manager.create(user_create)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def clear_table(session: AsyncSession, model):
        """Clear all records from a table."""
        await session.execute(f"DELETE FROM {model.__tablename__}")
        await session.commit()


@pytest.fixture
def db_utils():
    """Provide database testing utilities."""
    return DatabaseTestUtils