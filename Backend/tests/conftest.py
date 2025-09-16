"""
Pytest configuration and fixtures for LangPlug tests
Simplified to avoid circular import issues
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from types import SimpleNamespace
import asyncio
from datetime import datetime, timedelta

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure project venv site-packages are on sys.path
import venv_activator  # noqa: F401


@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests"""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session

@pytest.fixture
def mock_sync_db_session():
    """Mock synchronous database session for unit tests"""
    mock_session = Mock()
    mock_session.execute = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.close = Mock()
    return mock_session


@pytest.fixture
def mock_auth_service():
    """Mock authentication service for unit tests"""
    mock_auth = Mock()
    mock_auth.register_user = Mock(return_value=SimpleNamespace(
        id=1, username="testuser", is_superuser=False, is_active=True
    ))
    mock_auth.authenticate_user = Mock(return_value=SimpleNamespace(
        id=1, username="testuser", is_superuser=False, is_active=True
    ))
    mock_auth.create_access_token = Mock(return_value="mock_jwt_token_12345")
    mock_auth.get_token_expiry = Mock(return_value=datetime.now() + timedelta(hours=1))
    mock_auth.login = Mock(return_value=SimpleNamespace(
        session_token="test_token", 
        user=SimpleNamespace(id=1, username="testuser"),
        expires_at=datetime.now() + timedelta(hours=1)
    ))
    mock_auth.validate_session = Mock(return_value=SimpleNamespace(
        id=1, username="testuser", is_superuser=False, is_active=True
    ))
    mock_auth.verify_token = Mock(return_value={"user_id": 1, "username": "testuser"})
    mock_auth.logout = Mock(return_value=True)
    mock_auth.update_language_preferences = Mock(return_value=True)
    return mock_auth


@pytest.fixture
def sample_vocabulary():
    """Sample vocabulary data for testing"""
    return {
        "known_words": {"the", "and", "is", "in", "to", "of", "a", "that"},
        "learning_words": {"hello", "world", "example", "test"},
        "mastered_words": {"simple", "basic", "easy", "common"}
    }


@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application for unit tests"""
    mock_app = Mock()
    mock_app.dependency_overrides = {}
    return mock_app


@pytest.fixture  
def mock_test_client(mock_fastapi_app):
    """Mock TestClient for API integration tests"""
    mock_client = Mock()
    mock_client.get = Mock()
    mock_client.post = Mock() 
    mock_client.put = Mock()
    mock_client.delete = Mock()
    return mock_client


@pytest.fixture
async def async_client():
    """Async HTTP client for integration tests"""
    import httpx
    from httpx import ASGITransport
    from core.app import create_app
    from core.database import get_async_session
    from core.dependencies import get_auth_service
    from core.auth import get_user_db, get_user_manager
    from unittest.mock import AsyncMock, Mock
    import uuid
    from datetime import datetime
    
    # Create the app
    app = create_app()
    
    # Override dependencies with mocks for testing
    async def mock_get_db():
        users = {}  # Store users in-memory for this mock
        
        mock_session = AsyncMock()
        
        async def mock_execute(query):
            # Mock the result object that SQLAlchemy returns
            mock_result = Mock()
            
            # Check if this is a user creation query
            if hasattr(query, 'table') and hasattr(query.table, 'name') and query.table.name == 'user':
                # This is likely a user creation - check for duplicates
                if hasattr(query, 'values') and 'email' in query.values:
                    email = query.values['email']
                    if email in users:
                        mock_result.unique.return_value.scalar_one_or_none.return_value = Mock()  # Existing user
                        return mock_result
            
            mock_result.unique.return_value.scalar_one_or_none.return_value = None  # No existing user
            return mock_result
        
        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.add = Mock()
        mock_session.refresh = AsyncMock()
        return mock_session
    
    async def mock_get_user_db():
        """Mock user database for FastAPI-Users"""
        from core.auth import User
        users_by_email = {}  # Store users by email
        users_by_username = {}  # Store users by username
        
        mock_user_db = AsyncMock()
        
        async def mock_get_by_email(email: str):
            return users_by_email.get(email)
            
        async def mock_get_by_username(username: str):
            return users_by_username.get(username)
            
        async def mock_create(user_create):
            # Check for duplicate username
            if user_create["username"] in users_by_username:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="USERNAME_ALREADY_EXISTS")
            
            # Check for duplicate email
            if user_create["email"] in users_by_email:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="EMAIL_ALREADY_EXISTS")
            
            # Create a new user with the provided data
            user = User(
                id=uuid.uuid4(),
                username=user_create["username"],
                email=user_create["email"],
                hashed_password="hashed_password",  # Mock hashed password
                is_active=True,
                is_superuser=False,
                is_verified=False,
                created_at=datetime.now()
            )
            users_by_email[user_create["email"]] = user
            users_by_username[user_create["username"]] = user
            return user
            
        mock_user_db.get_by_email = mock_get_by_email
        mock_user_db.get_by_username = mock_get_by_username
        mock_user_db.create = mock_create
        return mock_user_db
    
    def mock_get_auth():
        users = {}  # Store users in-memory for this mock
        next_id = 1
        
        mock_auth = Mock()
        
        def mock_register_user(username: str, password: str, email: str):
            # Check if user already exists
            if email in users:
                raise ValueError("User already exists")
            
            # Create new user
            user = SimpleNamespace(
                id=next_id,
                username=username,
                is_superuser=False,
                is_active=True,
                created_at="2024-01-01T00:00:00Z"
            )
            users[email] = user
            next_id += 1
            return user
            
        mock_auth.register_user = mock_register_user
        return mock_auth
    
    app.dependency_overrides[get_async_session] = mock_get_db
    app.dependency_overrides[get_auth_service] = mock_get_auth
    app.dependency_overrides[get_user_db] = mock_get_user_db
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def client():
    """Real FastAPI TestClient for integration tests"""
    from fastapi.testclient import TestClient
    from core.app import create_app
    from core.database import get_async_session
    from core.dependencies import get_auth_service
    from core.auth import get_user_db, get_user_manager
    from unittest.mock import AsyncMock, Mock
    import uuid
    from datetime import datetime
    
    # Create the app
    app = create_app()
    
    # Override dependencies with mocks for testing
    async def mock_get_db():
        users = {}  # Store users in-memory for this mock
        
        mock_session = AsyncMock()
        
        async def mock_execute(query):
            # Mock the result object that SQLAlchemy returns
            mock_result = Mock()
            
            # Check if this is a user creation query
            if hasattr(query, 'table') and hasattr(query.table, 'name') and query.table.name == 'user':
                # This is likely a user creation - check for duplicates
                if hasattr(query, 'values') and 'email' in query.values:
                    email = query.values['email']
                    if email in users:
                        mock_result.unique.return_value.scalar_one_or_none.return_value = Mock()  # Existing user
                        return mock_result
            
            mock_result.unique.return_value.scalar_one_or_none.return_value = None  # No existing user
            return mock_result
        
        mock_session.execute = mock_execute
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.add = Mock()
        mock_session.refresh = AsyncMock()
        return mock_session
    
    async def mock_get_user_db():
        """Mock user database for FastAPI-Users"""
        from core.auth import User
        users_by_email = {}  # Store users by email
        users_by_username = {}  # Store users by username
        
        mock_user_db = AsyncMock()
        
        async def mock_get_by_email(email: str):
            return users_by_email.get(email)
            
        async def mock_get_by_username(username: str):
            return users_by_username.get(username)
            
        async def mock_create(user_create):
            # Check for duplicate username
            if user_create["username"] in users_by_username:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="USERNAME_ALREADY_EXISTS")
            
            # Check for duplicate email
            if user_create["email"] in users_by_email:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="EMAIL_ALREADY_EXISTS")
            
            # Create a new user with the provided data
            user = User(
                id=uuid.uuid4(),
                username=user_create["username"],
                email=user_create["email"],
                hashed_password="hashed_password",  # Mock hashed password
                is_active=True,
                is_superuser=False,
                is_verified=False,
                created_at=datetime.now()
            )
            users_by_email[user_create["email"]] = user
            users_by_username[user_create["username"]] = user
            return user
            
        mock_user_db.get_by_email = mock_get_by_email
        mock_user_db.get_by_username = mock_get_by_username
        mock_user_db.create = mock_create
        return mock_user_db
    
    def mock_get_auth():
        users = {}  # Store users in-memory for this mock
        next_id = 1
        
        mock_auth = Mock()
        
        def mock_register_user(username: str, password: str, email: str):
            # Check if user already exists
            if email in users:
                raise ValueError("User already exists")
            
            # Create new user
            user = SimpleNamespace(
                id=next_id,
                username=username,
                is_superuser=False,
                is_active=True,
                created_at="2024-01-01T00:00:00Z"
            )
            users[email] = user
            next_id += 1
            return user
            
        mock_auth.register_user = mock_register_user
        return mock_auth
    
    app.dependency_overrides[get_async_session] = mock_get_db
    app.dependency_overrides[get_auth_service] = mock_get_auth
    app.dependency_overrides[get_user_db] = mock_get_user_db
    
    return TestClient(app)
