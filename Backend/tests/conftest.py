"""
Pytest configuration and fixtures for LangPlug tests
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.database_manager import DatabaseManager

# Ensure project venv site-packages are on sys.path before importing FastAPI
import venv_activator  # noqa: F401

# Optional in-process TestClient for API tests
import httpx
from fastapi.testclient import TestClient
from core.app import create_app
from core.dependencies import get_database_manager, get_auth_service
from contextlib import asynccontextmanager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db_manager = DatabaseManager(db_path)
        # DatabaseManager creates schema on first use; no explicit init needed
        yield db_manager
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def mock_auth_service():
    """In-memory fake authentication service for API tests."""
    from datetime import datetime, timedelta
    
    class Fake:
        def __init__(self):
            self._users = {}
            self._tokens = {}
            self._next_id = 1
            # Seed a default token for tests that use a static header
            default_user = SimpleNamespace(
                id=self._next_id,
                username="testuser",
                is_admin=False,
                is_active=True,
                created_at=datetime.now().isoformat(),
                last_login=datetime.now().isoformat(),
                native_language="en",
                target_language="de",
            )
            self._users[default_user.username] = default_user
            self._tokens["test_token"] = default_user
            self._next_id += 1

        def register_user(self, username: str, password: str):
            if username in self._users:
                raise ValueError("User already exists")
            user = SimpleNamespace(
                id=self._next_id,
                username=username,
                is_admin=False,
                is_active=True,
                created_at=datetime.now().isoformat(),
                last_login=None,
                native_language="en",
                target_language="de",
            )
            self._next_id += 1
            self._users[username] = user
            return user

        def authenticate_user(self, username: str, password: str):
            if username == "nonexistent":
                return None
            if password.startswith("Wrong"):
                return None
            if username not in self._users:
                return self.register_user(username, password)
            user = self._users[username]
            user.last_login = datetime.now().isoformat()
            return user

        def create_access_token(self, user_id: int):
            return "mock_jwt_token_12345"

        def get_token_expiry(self):
            return datetime.now() + timedelta(hours=1)

        def login(self, username: str, password: str):
            # Check if user exists
            if username not in self._users:
                raise ValueError("Invalid username or password")
            
            user = self._users[username]
            # For testing, we'll accept any password that doesn't start with "Wrong"
            if password.startswith("Wrong"):
                raise ValueError("Invalid username or password")
            
            token = f"testtoken-{user.id}-{username}"
            self._tokens[token] = user
            user.last_login = datetime.now().isoformat()
            return SimpleNamespace(session_token=token, user=user, expires_at=datetime.now() + timedelta(hours=1))

        def validate_session(self, token: str):
            user = self._tokens.get(token)
            if not user:
                raise ValueError("Invalid or expired token")
            return user

        def verify_token(self, token: str):
            user = self._tokens.get(token)
            if not user:
                raise ValueError("Invalid or expired token")
            return {"user_id": user.id, "username": user.username}

        def logout(self, token: str) -> bool:
            return self._tokens.pop(token, None) is not None

        def update_language_preferences(self, user_id: int, native: str, target: str) -> bool:
            # Update on stored users
            for u in self._users.values():
                if u.id == user_id:
                    u.native_language = native
                    u.target_language = target
                    return True
            return False

    return Fake()


@pytest.fixture
def sample_vocabulary():
    """Sample vocabulary data for testing"""
    return {
        "known_words": {"the", "and", "is", "in", "to", "of", "a", "that"},
        "learning_words": {"hello", "world", "example", "test"},
        "mastered_words": {"simple", "basic", "easy", "common"}
    }


@pytest.fixture
def client(temp_db, mock_auth_service):
    """FastAPI TestClient with no-op lifespan and DI overrides.

    - Avoids hitting a live server (uses in-process app)
    - Uses a temporary initialized database
    - Injects a simple mock auth service
    """
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    # Disable heavy startup/shutdown
    app.router.lifespan_context = no_lifespan

    # Dependency overrides
    app.dependency_overrides[get_database_manager] = lambda: temp_db
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    # Use FastAPI TestClient instead of httpx.Client
    return TestClient(app)


@pytest.fixture
async def async_client(temp_db, mock_auth_service):
    """Async httpx client backed by ASGITransport for async tests."""
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_app):
        yield
    app.router.lifespan_context = no_lifespan

    app.dependency_overrides[get_database_manager] = lambda: temp_db
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
def ws_client(temp_db, mock_auth_service):
    """Starlette TestClient for WebSocket-specific tests."""
    app = create_app()

    @asynccontextmanager
    async def no_lifespan(_app):
        yield
    app.router.lifespan_context = no_lifespan

    app.dependency_overrides[get_database_manager] = lambda: temp_db
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    return TestClient(app)
