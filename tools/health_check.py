#!/usr/bin/env python3
"""
Server Health Check Utility

Simple utility to verify both backend and frontend servers are running
and accessible before running E2E tests.
"""

import httpx
import time
import sys
from typing import Optional


class HealthChecker:
    """Health check utility for LangPlug servers."""

    def __init__(self):
        self.backend_url = "http://127.0.0.1:8000"
        self.frontend_url = "http://localhost:3001"
        self.frontend_url_alt = "http://localhost:3000"  # Backup port

    def check_backend(self, timeout: int = 5) -> tuple[bool, str]:
        """Check if backend server is healthy."""
        try:
            response = httpx.get(f"{self.backend_url}/docs", timeout=timeout)
            if response.status_code == 200:
                return True, "Backend is healthy"
            else:
                return False, f"Backend returned status {response.status_code}"
        except httpx.ConnectError:
            return False, "Backend connection refused - server not running"
        except httpx.TimeoutException:
            return False, f"Backend timeout after {timeout}s"
        except Exception as e:
            return False, f"Backend error: {str(e)}"

    def check_frontend(self, timeout: int = 5) -> tuple[bool, str, Optional[str]]:
        """Check if frontend server is healthy. Returns (healthy, message, actual_url)."""
        # Try primary port first
        for url in [self.frontend_url, self.frontend_url_alt]:
            try:
                response = httpx.get(url, timeout=timeout)
                if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
                    return True, "Frontend is healthy", url
                else:
                    continue  # Try next URL
            except httpx.ConnectError:
                continue  # Try next URL
            except httpx.TimeoutException:
                continue  # Try next URL
            except Exception:
                continue  # Try next URL

        return False, "Frontend connection refused on both ports 3000 and 3001", None

    def wait_for_backend(self, max_wait: int = 30) -> bool:
        """Wait for backend to become healthy."""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            healthy, message = self.check_backend()
            if healthy:
                print(f"✅ {message}")
                return True
            print(f"⏳ Waiting for backend... ({message})")
            time.sleep(2)

        print(f"❌ Backend not ready after {max_wait}s")
        return False

    def wait_for_frontend(self, max_wait: int = 30) -> Optional[str]:
        """Wait for frontend to become healthy. Returns the actual URL if successful."""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            healthy, message, url = self.check_frontend()
            if healthy:
                print(f"✅ {message} at {url}")
                return url
            print(f"⏳ Waiting for frontend... ({message})")
            time.sleep(2)

        print(f"❌ Frontend not ready after {max_wait}s")
        return None

    def check_all(self) -> bool:
        """Check both servers are healthy."""
        backend_healthy, backend_msg = self.check_backend()
        frontend_healthy, frontend_msg, frontend_url = self.check_frontend()

        print("🏥 Server Health Check Results:")
        print(f"Backend:  {'✅' if backend_healthy else '❌'} {backend_msg}")
        print(f"Frontend: {'✅' if frontend_healthy else '❌'} {frontend_msg}")
        if frontend_healthy:
            print(f"Frontend URL: {frontend_url}")

        return backend_healthy and frontend_healthy

    def wait_for_all(self, max_wait: int = 30) -> tuple[bool, Optional[str]]:
        """Wait for both servers to become healthy."""
        print("🚀 Starting server health monitoring...")

        backend_ready = self.wait_for_backend(max_wait)
        frontend_url = self.wait_for_frontend(max_wait)

        all_ready = backend_ready and frontend_url is not None

        if all_ready:
            print("🎉 All servers are healthy and ready for E2E tests!")
        else:
            print("💥 Some servers are not ready")

        return all_ready, frontend_url


def main():
    """Command line interface for health checker."""
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        # Wait mode - for use in scripts
        checker = HealthChecker()
        all_ready, frontend_url = checker.wait_for_all(60)
        sys.exit(0 if all_ready else 1)
    else:
        # Quick check mode
        checker = HealthChecker()
        all_healthy = checker.check_all()
        sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
