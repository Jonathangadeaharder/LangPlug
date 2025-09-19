"""
Modern pytest configuration with proper test database isolation and fixtures.
Follows FastAPI and SQLAlchemy best practices for testing.
"""
import asyncio
import os
import uuid
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Set testing environment variable early and decide DB backend
os.environ["TESTING"] = "1"
from pathlib import Path
USE_TEST_POSTGRES = os.environ.get("USE_TEST_POSTGRES", "0") == "1"
if USE_TEST_POSTGRES:
    pg_url = os.environ.get(
        "TEST_POSTGRES_URL",
        "postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug",
    )
    os.environ["LANGPLUG_DB_TYPE"] = "postgresql"
    os.environ["LANGPLUG_DATABASE_URL"] = pg_url
else:
    # Force app-level database to a dedicated test SQLite file to unify engines
    TEST_DB_DIR = Path(__file__).parent / ".pytest-db"
    TEST_DB_DIR.mkdir(exist_ok=True)
    TEST_DB_PATH = str(TEST_DB_DIR / "test.db")
    os.environ["LANGPLUG_DB_TYPE"] = "sqlite"
    os.environ["LANGPLUG_DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
repo_root = project_root.parent

# Ensure both Backend and repository root are importable for tests that need management tooling.
for path in (repo_root, project_root):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)

from core.app import create_app
from core.auth import Base, User
from core.database import get_async_session
from database.models import Base as ModelsBase
from tests.utils.url_builder import get_url_builder

# Test database setup (same URL used by app-level engine)
if USE_TEST_POSTGRES:
    TEST_SYNC_DATABASE_URL = os.environ.get(
        "TEST_POSTGRES_URL",
        "postgresql://langplug_user:langplug_password@localhost:5432/langplug",
    )
else:
    TEST_SYNC_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"



@pytest.fixture(scope="function", autouse=True)
async def cleanup_async_tasks():
    """Automatically cleanup async tasks after each test to prevent 'Task was destroyed but it is pending' warnings."""
    yield
    
    # Simple task cleanup - just yield control to allow pending tasks to complete
    await asyncio.sleep(0.01)


@pytest.fixture(scope="function")
async def async_engine():
    """Create async database engine for testing."""
    if USE_TEST_POSTGRES:
        engine = create_async_engine(
            os.environ["LANGPLUG_DATABASE_URL"],
            pool_pre_ping=True,
            echo=False,
        )
    else:
        engine = create_async_engine(
            os.environ["LANGPLUG_DATABASE_URL"],
            connect_args={"check_same_thread": False},
            echo=False,
        )

    # Ensure a clean schema for this test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(ModelsBase.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ModelsBase.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh AsyncSession per test using the per-test engine.

    We avoid wrapping in an explicit transaction to prevent aiosqlite deadlocks
    under certain anyio/pytest lifecycles. Engine is per-test and disposed after,
    so data isolation is preserved without nested transaction complexity.
    """
    async_session_maker = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    session = async_session_maker()
    try:
        yield session
    finally:
        await session.close()
        # Ensure any remaining async operations are completed
        await asyncio.sleep(0)


@pytest.fixture
async def test_app(db_session):
    """Create FastAPI app with test database session override."""
    # Ensure testing environment is set
    os.environ["TESTING"] = "1"

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
        yield ac
        # Ensure client is properly closed and any pending tasks are handled
        await asyncio.sleep(0)


@pytest.fixture
async def test_user(db_session):
    """Create a test user for authentication tests."""
    import uuid

    # Create user directly in database
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        username="testuser",
        hashed_password="$2b$12$hashedpasswordplaceholder",  # Dummy hash
        is_active=True,
        is_superuser=False,
        is_verified=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def authenticated_user(test_user, test_app):
    """Create authenticated user with valid JWT token."""
    # For testing purposes, we'll create a mock token
    # In real tests, you might want to use the actual auth flow
    token = "mock_test_token_" + str(uuid.uuid4())

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
        import uuid

        defaults = {
            "id": uuid.uuid4(),
            "email": f"user_{uuid.uuid4().hex[:8]}@test.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "hashed_password": "$2b$12$hashedpasswordplaceholder",
            "is_verified": True,
            "is_active": True,
            "is_superuser": False
        }
        defaults.update(kwargs)

        user = User(**defaults)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def clear_table(session: AsyncSession, model):
        """Clear all records from a table."""
        from sqlalchemy import delete
        await session.execute(delete(model))
        await session.commit()


@pytest.fixture
def db_utils():
    """Provide database testing utilities."""
    return DatabaseTestUtils
