"""
In-memory pytest configuration for fast, reliable backend tests.
This configuration uses FastAPI's TestClient/httpx with dependency overrides
to run tests entirely in process (no external server).
"""

import os
import sys
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Ensure the Backend project root is on sys.path for imports like `core.app`
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.app import create_app

# Import fast fixtures (autouse fixtures will be applied automatically)
from tests.fixtures.fast_auth import *
from tests.fixtures.mock_services import *

# Force test mode and asyncio backend only in tests
os.environ["TESTING"] = "1"
os.environ["ANYIO_BACKEND"] = "asyncio"


# Override anyio backend selection to force asyncio
@pytest.fixture(autouse=True)
def force_asyncio_backend():
    """Force asyncio backend for all tests to eliminate trio duplicates"""
    import anyio

    if hasattr(anyio, "BACKENDS"):
        # Force asyncio as the only backend
        original_backends = anyio.BACKENDS
        anyio.BACKENDS = {"asyncio": anyio.BACKENDS["asyncio"]}
        yield
        anyio.BACKENDS = original_backends
    else:
        yield


# Clear lru_cache between tests to prevent state pollution
@pytest.fixture(scope="function", autouse=True)
def clear_service_caches():
    """
    Clear specific lru_cache decorated functions between tests.

    This prevents state pollution from cached service instances, registries,
    and other cached functions that would otherwise persist across tests.

    Critical for preventing "passes individually, fails in suite" flaky tests.
    """

    def safe_clear_caches():
        """
        Clear known lru_cache decorated functions.

        Only catches expected exceptions (ImportError, AttributeError).
        Follows fail-fast principle - unexpected exceptions will propagate.
        """
        cleared_count = 0

        try:
            from services.service_factory import get_service_registry

            if hasattr(get_service_registry, "cache_clear"):
                get_service_registry.cache_clear()
                cleared_count += 1
        except (ImportError, AttributeError):
            # Expected: module not found or function doesn't have cache_clear
            pass

        try:
            from core.task_dependencies import get_task_progress_registry

            # Clear registry contents between tests
            registry = get_task_progress_registry()
            registry.clear()
            cleared_count += 1
        except (ImportError, AttributeError):
            # Expected: module not found or registry doesn't exist
            pass

        # Note: get_translation_service and get_task_progress_registry
        # no longer use @lru_cache - removed to fix test isolation issues

        return cleared_count

    # Clear all caches before test
    # Note: Vocabulary services now use test-aware singleton pattern
    # and automatically create fresh instances in test mode (TESTING=1)
    safe_clear_caches()

    yield

    # Clear all caches after test
    safe_clear_caches()


# Ensure testing mode
os.environ["TESTING"] = "1"
# Force debug mode for tests to enable debug endpoints
os.environ["LANGPLUG_DEBUG"] = "true"
# Configure anyio to use only asyncio (disable trio for speed)
os.environ["ANYIO_BACKEND"] = "asyncio"
# Use fastest transcription model for tests (prevents timeouts)
os.environ["LANGPLUG_TRANSCRIPTION_SERVICE"] = "whisper-tiny"
# Use fastest translation model for tests (prevents timeouts)
os.environ["LANGPLUG_TRANSLATION_SERVICE"] = "opus-de-es"


# --- URL Builder using FastAPI's url_path_for (Type-Safe) ----------------
class URLBuilder:
    """
    Type-safe URL builder using FastAPI's url_path_for.
    Automatically syncs with route changes - no manual mapping needed.
    """

    def __init__(self, app):
        self.app = app

    def url_for(self, route_name: str, **path_params) -> str:
        """
        Generate URL for a named route using FastAPI's url_path_for.

        Args:
            route_name: The route name (from @router decorator)
            **path_params: Path parameters for the route

        Returns:
            Full URL path

        Example:
            url_for("get_vocabulary_stats")
            url_for("get_task_progress", task_id="abc123")
        """
        return self.app.url_path_for(route_name, **path_params)


@pytest.fixture
def url_builder(app) -> URLBuilder:
    """Provide a type-safe URL builder for tests using FastAPI's url_path_for."""
    return URLBuilder(app)


@pytest.fixture
def http_url_builder(url_builder: URLBuilder) -> URLBuilder:
    """Alias fixture for backward compatibility."""
    return url_builder


# --- Application + DB override ---------------------------------------------
@pytest.fixture(scope="function")
def app(tmp_path: Path) -> Generator[FastAPI, None, None]:
    """Create FastAPI app with per-test in-memory DB for maximum speed."""
    # Override settings before creating app to enable debug mode for tests
    from core.config import settings

    original_debug = settings.debug
    settings.debug = True

    try:
        # Build app
        application = create_app()

        # Use temporary file-based SQLite with shared cache for maximum speed
        # In-memory databases don't share state between sync and async connections
        import tempfile

        db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        sync_url = f"sqlite:///{db_file.name}?cache=shared"
        async_url = f"sqlite+aiosqlite:///{db_file.name}?cache=shared"

        # Ensure all models are registered on the unified Base
        import database.models  # noqa: F401 - Import all models
        from core.auth import User  # noqa: F401 - Import User model
        from core.database import Base

        # Create tables synchronously to avoid event loop complications
        sync_engine = create_sync_engine(sync_url, poolclass=StaticPool, connect_args={"check_same_thread": False})
        try:
            Base.metadata.create_all(bind=sync_engine)
        finally:
            sync_engine.dispose()

        # Async engine + sessionmaker for app dependency override
        async_engine = create_async_engine(
            async_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        SessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

        async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
            async with SessionLocal() as session:
                yield session

        # Apply dependency override
        import core.database as core_db

        application.dependency_overrides[core_db.get_async_session] = override_get_async_session

        # Store session factory for advanced test fixtures
        application.state._test_session_factory = SessionLocal

        # Expose engine for cleanup
        application.state._test_async_engine = async_engine

        yield application
    finally:
        # Cleanup: close engine and remove temp file
        import asyncio

        try:
            asyncio.run(async_engine.dispose())
        except:
            pass  # May already be disposed

        # Clean up temporary database file
        import os

        try:
            os.unlink(db_file.name)
        except:
            pass  # File may not exist or already be deleted

        # Restore original debug setting
        settings.debug = original_debug


# --- Clients (in-process) ---------------------------------------------------
@pytest.fixture
def http_client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Synchronous in-process client (keeps legacy name for compatibility)."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client(http_client: TestClient) -> Generator[TestClient, None, None]:
    """Alias for synchronous client used by many tests."""
    yield http_client


@pytest.fixture
async def async_http_client(app: FastAPI, base_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async in-process client (keeps legacy name for compatibility)."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def async_client(async_http_client: httpx.AsyncClient) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Alias for async client used by many tests."""
    yield async_http_client


# --- Misc helpers -----------------------------------------------------------
@pytest.fixture
def unique_user_data() -> dict:
    """Generate unique user data for tests."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def base_url() -> str:
    """Base URL used by in-memory httpx clients."""
    return "http://test"


# --- Multilingual vocabulary test fixtures ---------------------------------
@pytest.fixture
def sample_vocabulary_concepts() -> list[dict]:
    """Sample multilingual vocabulary concepts for testing."""
    from uuid import uuid4

    concept_1 = str(uuid4())
    concept_2 = str(uuid4())
    concept_3 = str(uuid4())

    return [
        {
            "id": concept_1,
            "difficulty_level": "A1",
            "semantic_category": "noun",
            "domain": "greeting",
            "translations": {"de": "Hallo", "es": "Hola", "en": "Hello"},
        },
        {
            "id": concept_2,
            "difficulty_level": "A2",
            "semantic_category": "verb",
            "domain": "communication",
            "translations": {"de": "sprechen", "es": "hablar", "en": "speak"},
        },
        {
            "id": concept_3,
            "difficulty_level": "B1",
            "semantic_category": "noun",
            "domain": "family",
            "gender": "das",
            "translations": {"de": "Mädchen", "es": "niña", "en": "girl"},
        },
    ]


@pytest.fixture
def sample_languages() -> list[dict]:
    """Sample supported languages for testing."""
    return [
        {"code": "de", "name": "German", "native_name": "Deutsch", "is_active": True},
        {"code": "es", "name": "Spanish", "native_name": "Español", "is_active": True},
        {"code": "en", "name": "English", "native_name": "English", "is_active": True},
        {"code": "fr", "name": "French", "native_name": "Français", "is_active": False},
    ]


@pytest.fixture
def sample_user_progress() -> dict:
    """Sample user learning progress for testing."""
    from datetime import datetime
    from uuid import uuid4

    concept_1 = str(uuid4())
    concept_2 = str(uuid4())

    return {
        "user_id": 1,
        "known_concepts": [
            {
                "concept_id": concept_1,
                "confidence_level": 5,
                "learned_at": datetime.utcnow().isoformat(),
                "review_count": 3,
                "last_reviewed": datetime.utcnow().isoformat(),
            }
        ],
        "unknown_concepts": [concept_2],
    }


@pytest.fixture
def multilingual_vocabulary_stats() -> dict:
    """Sample multilingual vocabulary statistics for testing."""
    return {
        "levels": {
            "A1": {"total_words": 100, "user_known": 25},
            "A2": {"total_words": 150, "user_known": 30},
            "B1": {"total_words": 200, "user_known": 20},
            "B2": {"total_words": 250, "user_known": 10},
            "C1": {"total_words": 300, "user_known": 5},
            "C2": {"total_words": 350, "user_known": 2},
        },
        "target_language": "de",
        "translation_language": "es",
        "total_words": 1350,
        "total_known": 92,
    }


@pytest.fixture
def vocabulary_level_response() -> dict:
    """Sample vocabulary level response for testing."""
    from uuid import uuid4

    concept_1 = str(uuid4())
    concept_2 = str(uuid4())

    return {
        "level": "A1",
        "target_language": "de",
        "translation_language": "es",
        "words": [
            {
                "concept_id": concept_1,
                "word": "Hallo",
                "translation": "Hola",
                "lemma": "hallo",
                "difficulty_level": "A1",
                "semantic_category": "noun",
                "domain": "greeting",
                "known": False,
            },
            {
                "concept_id": concept_2,
                "word": "Welt",
                "translation": "mundo",
                "lemma": "welt",
                "difficulty_level": "A1",
                "semantic_category": "noun",
                "domain": "geography",
                "known": True,
            },
        ],
        "total_count": 100,
        "known_count": 25,
    }


# --- Transaction Isolation Fixtures for Robust Testing ---
@pytest.fixture
async def isolated_db_session(app: FastAPI) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session with transaction rollback for complete isolation.

    This fixture creates a transaction, runs the test, then rolls back all changes,
    ensuring no test state persists between tests.
    """
    session_factory = app.state._test_session_factory

    async with session_factory() as session:
        # Start a transaction
        transaction = await session.begin()

        try:
            yield session
        finally:
            # Always rollback the transaction, regardless of test outcome
            await transaction.rollback()


@pytest.fixture
def db_session_override(app: FastAPI, isolated_db_session: AsyncSession):
    """
    Override the app's database session with an isolated session.

    Use this fixture in tests that need guaranteed database isolation.
    """

    async def override_get_isolated_session():
        yield isolated_db_session

    # Override the database dependency
    import core.database as core_db

    original_override = app.dependency_overrides.get(core_db.get_async_session)
    app.dependency_overrides[core_db.get_async_session] = override_get_isolated_session

    try:
        yield isolated_db_session
    finally:
        # Restore original override
        if original_override:
            app.dependency_overrides[core_db.get_async_session] = original_override
        else:
            app.dependency_overrides.pop(core_db.get_async_session, None)


# --- Test State Monitoring and Pollution Detection ---
@pytest.fixture(autouse=True)
def test_pollution_detector():
    """
    Automatically detect test pollution and mock state leakage.

    Performance optimization: Only run pollution detection when explicitly enabled
    via PYTEST_DETECT_POLLUTION environment variable.
    """
    import os

    # Skip expensive pollution detection unless explicitly enabled
    if os.environ.get("PYTEST_DETECT_POLLUTION", "").lower() not in ("1", "true", "yes"):
        yield
        return

    import gc
    import warnings

    # Store initial state - count mock objects (expensive operation)
    initial_mock_state = len([obj for obj in gc.get_objects() if isinstance(obj, (MagicMock, AsyncMock))])

    yield

    # Check for mock pollution after test (expensive operation)
    final_mock_state = len([obj for obj in gc.get_objects() if isinstance(obj, (MagicMock, AsyncMock))])

    # Warn if significant mock object increase (potential pollution)
    if final_mock_state > initial_mock_state + 50:
        warnings.warn(
            f"Potential mock pollution detected: {final_mock_state - initial_mock_state} mock objects created",
            category=UserWarning,
            stacklevel=2,
        )


@pytest.fixture
def clean_mock_session():
    """
    Provide a completely fresh mock session with guaranteed isolation.

    This ensures no mock state carries over between tests.
    """
    from tests.base import DatabaseTestBase

    # Create fresh mock session
    mock_session = DatabaseTestBase.create_mock_session()

    yield mock_session

    # Explicit cleanup (though Python GC should handle this)
    del mock_session


# --- Database State Cleanup Fixtures ---
@pytest.fixture
async def clean_database(app: FastAPI):
    """
    Provide a completely clean database state for each test.

    This fixture truncates all tables before and after each test,
    ensuring no residual data affects test outcomes.
    """
    session_factory = app.state._test_session_factory

    async def cleanup_all_tables():
        """Remove all data from all tables while preserving schema."""
        from core.database import Base

        async with session_factory() as session:
            # Get all table names from metadata
            table_names = [table.name for table in reversed(Base.metadata.sorted_tables)]

            try:
                # Disable foreign key constraints for cleanup (SQLite specific)
                if "sqlite" in str(session.bind.url):
                    await session.execute("PRAGMA foreign_keys = OFF")

                # Truncate all tables
                for table_name in table_names:
                    await session.execute("DELETE FROM " + table_name)

                await session.commit()

                # Re-enable foreign key constraints
                if "sqlite" in str(session.bind.url):
                    await session.execute("PRAGMA foreign_keys = ON")

            except Exception as e:
                await session.rollback()
                import warnings

                warnings.warn(f"Database cleanup failed: {e}", UserWarning, stacklevel=2)

    # Clean before test
    await cleanup_all_tables()

    yield

    # Clean after test
    await cleanup_all_tables()


@pytest.fixture
async def seeded_database(clean_database, app: FastAPI):
    """
    Provide a database with consistent test seed data.

    This fixture creates a standard set of test data that tests can rely on,
    while still maintaining isolation through the clean_database fixture.
    """
    session_factory = app.state._test_session_factory

    async with session_factory() as session:
        from datetime import datetime

        from core.auth import User

        # Create test users
        test_users = [
            User(
                email="testuser1@example.com",
                username="testuser1",
                hashed_password="fake_hash_1",
                is_active=True,
                is_superuser=False,
                is_verified=True,
                created_at=datetime.now(),
            ),
            User(
                email="testuser2@example.com",
                username="testuser2",
                hashed_password="fake_hash_2",
                is_active=True,
                is_superuser=False,
                is_verified=True,
                created_at=datetime.now(),
            ),
            User(
                email="admin@example.com",
                username="admin_test",
                hashed_password="fake_hash_admin",
                is_active=True,
                is_superuser=True,
                is_verified=True,
                created_at=datetime.now(),
            ),
        ]

        for user in test_users:
            session.add(user)

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            import warnings

            warnings.warn(f"Database seeding failed: {e}", UserWarning, stacklevel=2)

    yield


@pytest.fixture
def database_state_validator():
    """
    Validate database state consistency before and after tests.

    This fixture can detect database state corruption and inconsistencies
    that might affect test reliability.
    """

    async def validate_state(app: FastAPI, description: str = ""):
        """Validate current database state."""
        session_factory = app.state._test_session_factory

        async with session_factory() as session:
            try:
                # Check basic database connectivity
                await session.execute("SELECT 1")

                # Validate foreign key consistency (SQLite specific)
                if "sqlite" in str(session.bind.url):
                    result = await session.execute("PRAGMA foreign_key_check")
                    violations = result.fetchall()
                    if violations:
                        import warnings

                        warnings.warn(
                            f"Foreign key violations detected {description}: {violations}", UserWarning, stacklevel=2
                        )

                # Check for unexpected table locks or transactions
                await session.commit()

            except Exception as e:
                import warnings

                warnings.warn(f"Database state validation failed {description}: {e}", UserWarning, stacklevel=2)

    return validate_state


# --- Session Factory Pattern for Consistent Test Architecture ---
class TestSessionFactory:
    """
    Factory for creating consistent database sessions and mocks across all tests.

    This factory encapsulates the complexity of session creation and provides
    standardized patterns for different test scenarios.
    """

    @staticmethod
    def create_real_session(app: FastAPI) -> AsyncSession:
        """Create a real database session for integration tests."""
        session_factory = app.state._test_session_factory
        return session_factory()

    @staticmethod
    def create_mock_session(isolation_level: str = "standard") -> AsyncMock:
        """
        Create a mock session with specified isolation level.

        Args:
            isolation_level: "minimal", "standard", or "enhanced"
                - minimal: Basic mock with no tracking
                - standard: Standard mock with basic isolation
                - enhanced: Full isolation with tracking and validation
        """
        from tests.base import DatabaseTestBase

        if isolation_level in {"minimal", "standard"}:
            return DatabaseTestBase.create_mock_session()
        elif isolation_level == "enhanced":
            return DatabaseTestBase.create_isolated_mock_session()
        else:
            raise ValueError(f"Unknown isolation level: {isolation_level}")

    @staticmethod
    def create_transactional_session(app: FastAPI) -> AsyncSession:
        """
        Create a real session wrapped in a transaction for complete rollback.

        This session will automatically rollback all changes when the test completes,
        ensuring perfect isolation between tests.
        """
        # This returns the isolated_db_session fixture functionality
        # Implementation would need to be coordinated with the fixture system
        raise NotImplementedError("Use isolated_db_session fixture instead")


@pytest.fixture
def session_factory():
    """Provide the TestSessionFactory for easy access in tests."""
    return TestSessionFactory


@pytest.fixture
async def seeded_vocabulary(app):
    """
    Seed test database with vocabulary words for integration tests.

    Creates vocabulary words across multiple difficulty levels (A1, A2, B1)
    so that vocabulary workflow tests have data to work with.
    """
    from database.models import VocabularyWord

    # Get the test session factory from the app
    SessionLocal = app.state._test_session_factory

    async with SessionLocal() as session:
        # Create vocabulary words across different levels
        words = [
            # A1 level words (10 words)
            VocabularyWord(
                word="Hallo",
                lemma="hallo",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                translation_en="Hello",
                translation_native="Hola",
            ),
            VocabularyWord(
                word="ich",
                lemma="ich",
                language="de",
                difficulty_level="A1",
                part_of_speech="pronoun",
                translation_en="I",
                translation_native="yo",
            ),
            VocabularyWord(
                word="du",
                lemma="du",
                language="de",
                difficulty_level="A1",
                part_of_speech="pronoun",
                translation_en="you",
                translation_native="tú",
            ),
            VocabularyWord(
                word="ja",
                lemma="ja",
                language="de",
                difficulty_level="A1",
                part_of_speech="adverb",
                translation_en="yes",
                translation_native="sí",
            ),
            VocabularyWord(
                word="nein",
                lemma="nein",
                language="de",
                difficulty_level="A1",
                part_of_speech="adverb",
                translation_en="no",
                translation_native="no",
            ),
            VocabularyWord(
                word="danke",
                lemma="danke",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                translation_en="thanks",
                translation_native="gracias",
            ),
            VocabularyWord(
                word="bitte",
                lemma="bitte",
                language="de",
                difficulty_level="A1",
                part_of_speech="adverb",
                translation_en="please",
                translation_native="por favor",
            ),
            VocabularyWord(
                word="gut",
                lemma="gut",
                language="de",
                difficulty_level="A1",
                part_of_speech="adjective",
                translation_en="good",
                translation_native="bueno",
            ),
            VocabularyWord(
                word="Mann",
                lemma="mann",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                gender="der",
                translation_en="man",
                translation_native="hombre",
            ),
            VocabularyWord(
                word="Frau",
                lemma="frau",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                gender="die",
                translation_en="woman",
                translation_native="mujer",
            ),
            # A2 level words (5 words)
            VocabularyWord(
                word="sprechen",
                lemma="sprechen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="speak",
                translation_native="hablar",
            ),
            VocabularyWord(
                word="verstehen",
                lemma="verstehen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="understand",
                translation_native="entender",
            ),
            VocabularyWord(
                word="lernen",
                lemma="lernen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="learn",
                translation_native="aprender",
            ),
            VocabularyWord(
                word="arbeiten",
                lemma="arbeiten",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="work",
                translation_native="trabajar",
            ),
            VocabularyWord(
                word="wohnen",
                lemma="wohnen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="live",
                translation_native="vivir",
            ),
            # B1 level words (5 words)
            VocabularyWord(
                word="Mädchen",
                lemma="mädchen",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="das",
                translation_en="girl",
                translation_native="niña",
            ),
            VocabularyWord(
                word="Junge",
                lemma="junge",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="der",
                translation_en="boy",
                translation_native="niño",
            ),
            VocabularyWord(
                word="Familie",
                lemma="familie",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="die",
                translation_en="family",
                translation_native="familia",
            ),
            VocabularyWord(
                word="Schule",
                lemma="schule",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="die",
                translation_en="school",
                translation_native="escuela",
            ),
            VocabularyWord(
                word="Arbeit",
                lemma="arbeit",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="die",
                translation_en="work",
                translation_native="trabajo",
            ),
        ]

        session.add_all(words)
        await session.commit()

        # Return the words for tests that need them
        return words
