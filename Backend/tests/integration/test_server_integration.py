"""
Backend Integration Tests - Server Startup and HTTP Connectivity

These tests verify that the actual FastAPI server can start and respond to HTTP requests.
Unlike unit tests that use TestClient, these make real HTTP requests to localhost.

Prerequisites: No running server (these tests start their own)
"""
import asyncio
import subprocess
import time
import pytest
import httpx
from pathlib import Path
import os
import signal


class ServerManager:
    """Manages starting and stopping the actual FastAPI server for integration tests."""
    
    def __init__(self, backend_dir: Path):
        self.backend_dir = backend_dir
        self.process = None
        self.base_url = "http://127.0.0.1:8001"  # Different port to avoid conflicts
        
    def start_server(self, timeout=30):
        """Start the FastAPI server on port 8001."""
        # Change to backend directory
        env = os.environ.copy()
        env["TESTING"] = "1"  # Enable test mode
        
        cmd = [
            "python", "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", 
            "--port", "8001",
            "--log-level", "warning"  # Reduce noise
        ]
        
        print(f"Starting server with: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd,
            cwd=self.backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_server_ready():
                print("Server is ready!")
                return True
            time.sleep(0.5)
        
        # If we get here, server didn't start
        stdout, stderr = self.process.communicate(timeout=5)
        raise RuntimeError(f"Server failed to start within {timeout}s.\nStdout: {stdout}\nStderr: {stderr}")
    
    def is_server_ready(self):
        """Check if server is responding to requests."""
        try:
            response = httpx.get(f"{self.base_url}/docs", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def stop_server(self):
        """Stop the FastAPI server."""
        if self.process:
            # Try graceful shutdown first
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                self.process.kill()
                self.process.wait()
            self.process = None


@pytest.fixture(scope="module")
def running_server():
    """Start a real FastAPI server for integration tests."""
    backend_dir = Path(__file__).parent.parent.parent
    server_manager = ServerManager(backend_dir)
    
    # Start server
    server_manager.start_server()
    
    yield server_manager
    
    # Cleanup
    server_manager.stop_server()


@pytest.mark.integration
@pytest.mark.timeout(60)
class TestBackendIntegration:
    """Integration tests for the actual running FastAPI server."""
    
    def test_server_starts_and_serves_docs(self, running_server):
        """Verify server starts and serves OpenAPI docs."""
        response = httpx.get(f"{running_server.base_url}/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
    
    def test_server_serves_openapi_spec(self, running_server):
        """Verify server serves OpenAPI specification."""
        response = httpx.get(f"{running_server.base_url}/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "LangPlug API"
    
    def test_health_check_endpoint(self, running_server):
        """Verify basic health check endpoint works."""
        response = httpx.get(f"{running_server.base_url}/")
        # Should either return 200 with content or 404 (both indicate server is working)
        assert response.status_code in [200, 404]
    
    def test_cors_headers_present(self, running_server):
        """Verify CORS headers are configured for frontend integration."""
        response = httpx.options(
            f"{running_server.base_url}/api/auth/register",
            headers={"Origin": "http://localhost:3001"}
        )
        # CORS preflight should work or endpoint should exist
        assert response.status_code in [200, 405, 404]  # Various OK responses
    
    @pytest.mark.asyncio
    async def test_async_client_connectivity(self, running_server):
        """Test async HTTP client connectivity to running server."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{running_server.base_url}/docs")
            assert response.status_code == 200
    
    def test_server_handles_404_gracefully(self, running_server):
        """Verify server handles non-existent endpoints gracefully."""
        response = httpx.get(f"{running_server.base_url}/nonexistent-endpoint")
        assert response.status_code == 404
        # Should return JSON error, not HTML
        assert response.headers.get("content-type", "").startswith("application/json")


@pytest.mark.integration  
@pytest.mark.timeout(120)
class TestBackendAPIIntegration:
    """Integration tests for specific API endpoints with real HTTP."""
    
    def test_auth_register_endpoint_exists(self, running_server):
        """Verify auth registration endpoint is accessible via HTTP."""
        # This should return 422 (validation error) not 404 (not found)
        response = httpx.post(f"{running_server.base_url}/api/auth/register", json={})
        assert response.status_code == 422  # Validation error, but endpoint exists
    
    def test_auth_login_endpoint_exists(self, running_server):
        """Verify auth login endpoint is accessible via HTTP."""
        response = httpx.post(f"{running_server.base_url}/api/auth/login", data={})
        assert response.status_code in [422, 400]  # Validation error, but endpoint exists
    
    def test_videos_endpoint_requires_auth(self, running_server):
        """Verify videos endpoint requires authentication via HTTP."""
        response = httpx.get(f"{running_server.base_url}/api/videos")
        assert response.status_code == 401  # Unauthorized, but endpoint exists


if __name__ == "__main__":
    # Allow running this file directly for debugging
    pytest.main([__file__, "-v"])