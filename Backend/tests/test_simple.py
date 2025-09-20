import pytest
from fastapi.testclient import TestClient
from core.app import create_app

@pytest.mark.timeout(30)
def test_Whenapp_creationCalled_ThenSucceeds():
    """Test that the app can be created without database initialization issues."""
    app = create_app()
    assert app is not None
    assert app.title == "LangPlug API"

@pytest.mark.timeout(30)
def test_Whenhealth_endpointCalled_ThenSucceeds():
    """Test the health endpoint."""
    if __import__('os').environ.get('SKIP_DB_HEAVY_TESTS') == '1':
        pytest.skip("Skipping client-based health check in constrained sandbox")
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
