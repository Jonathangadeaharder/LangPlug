"""
Pytest configuration and fixtures for LangPlug tests
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.database_manager import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db_manager = DatabaseManager(db_path)
        db_manager._create_database()  # Use the private method to create schema
        yield db_manager
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def mock_auth_service():
    """Mock authentication service for testing"""
    mock = Mock()
    mock.verify_token.return_value = {"user_id": "test_user_123", "username": "testuser"}
    mock.create_session.return_value = ("test_session_id", "test_token")
    return mock


@pytest.fixture
def sample_vocabulary():
    """Sample vocabulary data for testing"""
    return {
        "known_words": {"the", "and", "is", "in", "to", "of", "a", "that"},
        "learning_words": {"hello", "world", "example", "test"},
        "mastered_words": {"simple", "basic", "easy", "common"}
    }