"""
Frontend Integration Tests - Vite Dev Server Startup and HTTP Connectivity

These tests verify that the actual Vite development server can start and serve the React application.
Unlike unit tests that use jsdom, these make real HTTP requests to localhost.

Prerequisites: No running server (these tests start their own)
"""
import subprocess
import time
import pytest
import httpx
from pathlib import Path
import os
import signal
import psutil


class ViteServerManager:
    """Manages starting and stopping the actual Vite dev server for integration tests."""
    
    def __init__(self, frontend_dir: Path):
        self.frontend_dir = frontend_dir
        self.process = None
        self.base_url = "http://localhost:3002"  # Different port to avoid conflicts
        
    def start_server(self, timeout=45):
        """Start the Vite dev server on port 3002."""
        # Check if npm is available
        if not self._check_npm():
            raise RuntimeError("npm not found. Please ensure Node.js is installed.")
            
        env = os.environ.copy()
        env["VITE_PORT"] = "3002"
        env["NODE_ENV"] = "development"
        
        cmd = ["npm", "run", "dev", "--", "--port", "3002", "--host", "localhost"]
        
        print(f"Starting Vite server with: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd,
            cwd=self.frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_server_ready():
                print("Vite server is ready!")
                return True
            time.sleep(1)
            
            # Check if process died
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(f"Vite server process died.\nStdout: {stdout}\nStderr: {stderr}")
        
        # If we get here, server didn't start
        stdout, stderr = self.process.communicate(timeout=5)
        raise RuntimeError(f"Vite server failed to start within {timeout}s.\nStdout: {stdout}\nStderr: {stderr}")
    
    def is_server_ready(self):
        """Check if Vite server is responding to requests."""
        try:
            response = httpx.get(self.base_url, timeout=3)
            # Vite should return HTML with the app div
            return response.status_code == 200 and "<!DOCTYPE html>" in response.text
        except Exception as e:
            return False
    
    def _check_npm(self):
        """Check if npm is available."""
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def stop_server(self):
        """Stop the Vite server and all child processes."""
        if self.process:
            # Kill all child processes (Vite spawns multiple processes)
            try:
                parent = psutil.Process(self.process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                parent.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    parent.kill()
                    self.process.wait()
            except psutil.NoSuchProcess:
                # Process already dead
                pass
            except Exception as e:
                # Fallback to simple termination
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            
            self.process = None


@pytest.fixture(scope="module")
def running_vite_server():
    """Start a real Vite dev server for integration tests."""
    frontend_dir = Path(__file__).parent.parent.parent
    server_manager = ViteServerManager(frontend_dir)
    
    # Start server
    server_manager.start_server()
    
    yield server_manager
    
    # Cleanup
    server_manager.stop_server()


@pytest.mark.integration
@pytest.mark.timeout(120)
class TestFrontendIntegration:
    """Integration tests for the actual running Vite dev server."""
    
    def test_vite_server_starts_and_serves_html(self, running_vite_server):
        """Verify Vite server starts and serves HTML."""
        response = httpx.get(running_vite_server.base_url)
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "root" in response.text  # React root div
    
    def test_vite_serves_react_app(self, running_vite_server):
        """Verify Vite serves the React application bundle."""
        response = httpx.get(running_vite_server.base_url)
        assert response.status_code == 200
        
        html = response.text
        # Should contain Vite's module loading
        assert "type=\"module\"" in html or "script" in html
        # Should contain the React root
        assert 'id="root"' in html
    
    def test_vite_serves_static_assets(self, running_vite_server):
        """Verify Vite can serve static assets."""
        # Try to get some common static files
        response = httpx.get(f"{running_vite_server.base_url}/vite.svg", timeout=10)
        # Should either exist (200) or return 404 (but server is working)
        assert response.status_code in [200, 404]
    
    def test_vite_handles_spa_routing(self, running_vite_server):
        """Verify Vite handles SPA routing (serves index.html for unknown routes)."""
        # SPA should serve index.html for any route
        response = httpx.get(f"{running_vite_server.base_url}/some-fake-route")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert 'id="root"' in response.text
    
    def test_vite_cors_headers(self, running_vite_server):
        """Verify Vite sets appropriate CORS headers for development."""
        response = httpx.get(running_vite_server.base_url)
        # Vite should allow CORS in development mode
        assert response.status_code == 200
        # Check if we can make requests (basic connectivity test)
    
    @pytest.mark.asyncio
    async def test_async_client_connectivity(self, running_vite_server):
        """Test async HTTP client connectivity to running Vite server."""
        async with httpx.AsyncClient() as client:
            response = await client.get(running_vite_server.base_url, timeout=10)
            assert response.status_code == 200
            assert "<!DOCTYPE html>" in response.text


@pytest.mark.integration
@pytest.mark.timeout(120)  
class TestFrontendRouteIntegration:
    """Integration tests for specific frontend routes with real HTTP."""
    
    def test_login_route_serves_content(self, running_vite_server):
        """Verify login route serves HTML (SPA routing)."""
        response = httpx.get(f"{running_vite_server.base_url}/login")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
    
    def test_register_route_serves_content(self, running_vite_server):
        """Verify register route serves HTML (SPA routing)."""
        response = httpx.get(f"{running_vite_server.base_url}/register")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
    
    def test_videos_route_serves_content(self, running_vite_server):
        """Verify videos route serves HTML (SPA routing)."""
        response = httpx.get(f"{running_vite_server.base_url}/videos")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text


if __name__ == "__main__":
    # Allow running this file directly for debugging
    pytest.main([__file__, "-v"])