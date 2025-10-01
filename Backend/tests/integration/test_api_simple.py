"""
Simple integration tests using FastAPI TestClient.
These tests verify that the API endpoints work correctly without external server setup.
"""

import pytest
from fastapi.testclient import TestClient

from core.app import create_app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    app = create_app()
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(client):
    """Test that health endpoint returns correct response."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.integration
def test_test_endpoint(client):
    """Test that test endpoint is accessible."""
    response = client.get("/test")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "timestamp" in data


@pytest.mark.integration
def test_docs_endpoint(client):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.integration
def test_openapi_endpoint(client):
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "LangPlug API"


@pytest.mark.integration
def test_protected_endpoint_without_auth(client):
    """Test that protected endpoints require authentication."""
    response = client.get("/api/vocabulary/")
    # Should return 401, 403, or 404 for unauthorized access to protected endpoints
    assert response.status_code in [401, 403, 404]


@pytest.mark.integration
def test_nonexistent_endpoint(client):
    """Test that nonexistent endpoints return 404."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
