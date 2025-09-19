"""
Pytest configuration for robust URL testing framework.
This provides common fixtures and configurations for all robust tests.
"""
import sys
from pathlib import Path

import pytest

# Add Backend directory to Python path for all tests
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient

from main import app
from tests.utils.url_builder import get_url_builder


@pytest.fixture(scope="session")
def test_app():
    """Application fixture for testing"""
    return app


@pytest.fixture
def client(test_app):
    """Test client fixture"""
    return TestClient(test_app)


@pytest.fixture
def url_builder(client):
    """URL builder fixture for robust URL generation"""
    return get_url_builder(client.app)


@pytest.fixture
def auth_headers():
    """Mock auth headers for testing (adjust based on your auth system)"""
    return {"Authorization": "Bearer mock_token_for_testing"}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers and settings"""
    config.addinivalue_line(
        "markers", "robust: mark test as using robust URL patterns"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance-related"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Auto-mark tests in robust directory
        if "robust" in str(item.fspath):
            item.add_marker(pytest.mark.robust)

        # Auto-mark auth tests
        if "auth" in item.name.lower() or "auth" in str(item.fspath):
            item.add_marker(pytest.mark.auth)

        # Auto-mark performance tests
        if "performance" in item.name.lower() or "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Auto-mark security tests
        if "security" in item.name.lower() or "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
