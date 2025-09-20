"""
In-memory pytest configuration for fast, reliable backend tests.
This configuration uses FastAPI's TestClient/httpx with dependency overrides
to run tests entirely in process (no external server).
"""
import os
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.app import create_app

# Ensure testing mode
os.environ["TESTING"] = "1"


# --- Lightweight URL builder (no network) ---------------------------------
class SimpleURLBuilder:
    """Minimal URL builder for tests that referenced http_url_builder.
    Avoids network calls and OpenAPI discovery by using a static mapping.
    """
    _routes = {
        # Auth
        "auth_register": "/api/auth/register",
        "auth_login": "/api/auth/login",
        "auth_logout": "/api/auth/logout",
        "auth_me": "/api/auth/me",
        # Processing
        "transcribe_video": "/api/process/transcribe",
        "filter_subtitles": "/api/process/filter-subtitles",
        "get_task_progress": "/api/process/progress/{task_id}",
        "process_chunk": "/api/process/chunk",
        # Videos
        "get_videos": "/api/videos",
        # Profile
        "profile_get": "/api/profile",
        "profile_update_languages": "/api/profile/languages",
        "profile_get_supported_languages": "/api/profile/languages",
        # Vocabulary
        "get_vocabulary_stats": "/api/vocabulary/stats",
        "get_blocking_words": "/api/vocabulary/blocking-words",
        "mark_word_known": "/api/vocabulary/mark-known",
        "preload_vocabulary": "/api/vocabulary/preload",
        "get_library_stats": "/api/vocabulary/library/stats",
        "get_vocabulary_level": "/api/vocabulary/library/{level}",
        "bulk_mark_level": "/api/vocabulary/library/bulk-mark",
    }

    def url_for(self, route_name: str, **path_params) -> str:
        if route_name not in self._routes:
            raise ValueError(f"Unknown route name: {route_name}")
        url = self._routes[route_name]
        for k, v in path_params.items():
            url = url.replace("{" + k + "}", str(v))
        return url


@pytest.fixture
def http_url_builder() -> SimpleURLBuilder:
    """Provide a simple, in-memory URL builder for tests."""
    return SimpleURLBuilder()


@pytest.fixture
def url_builder(http_url_builder: SimpleURLBuilder) -> SimpleURLBuilder:
    """Alias fixture for tests expecting 'url_builder'."""
    return http_url_builder


# --- Application + DB override ---------------------------------------------
@pytest.fixture(scope="function")
def app(tmp_path: Path) -> Generator[FastAPI, None, None]:
    """Create FastAPI app with per-test SQLite DB and dependency overrides."""
    # Build app
    application = create_app()

    # Prepare per-test SQLite database file
    db_file = tmp_path / "test.db"
    sync_url = f"sqlite:///{db_file}"
    async_url = f"sqlite+aiosqlite:///{db_file}"

    # Ensure all models are registered on the shared Base
    import database.models  # noqa: F401
    from core.auth import Base as AuthBase
    # Create tables synchronously to avoid event loop complications
    sync_engine = create_sync_engine(sync_url)
    try:
        AuthBase.metadata.create_all(bind=sync_engine)
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

    # Expose engine for cleanup
    application.state._test_async_engine = async_engine

    try:
        yield application
    finally:
        # Dispose async engine
        import asyncio
        try:
            asyncio.run(async_engine.dispose())
        except RuntimeError:
            # Event loop already running (e.g., in anyio) – best-effort cleanup
            pass


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
