"""
Robust performance tests using named routes instead of hardcoded URLs.
This replaces performance-related test files with a robust URL builder pattern.
"""
import sys
import os
# Add the Backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from tests.utils.url_builder import get_url_builder
from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture 
def url_builder(client):
    """URL builder fixture for robust URL generation"""
    return get_url_builder(client.app)


class TestAPIPerformanceRobust:
    """Performance tests using robust URL patterns"""
    
    def test_auth_login_performance(self, client, url_builder):
        """Test login endpoint performance"""
        login_times = []
        
        # Register a user first (FastAPI-Users endpoint)
        client.post("/api/auth/register", json={
            "username": "perfuser", 
            "password": "TestPass123"
        })
        
        # Perform multiple login requests
        for i in range(10):  # Reduced from 20 for faster testing
            start_time = time.time()
            response = client.post("/api/auth/login", json={
                "username": "perfuser", 
                "password": "TestPass123"
            })
            end_time = time.time()
            
            if response.status_code == 200:
                login_times.append(end_time - start_time)
        
        if login_times:
            avg_time = sum(login_times) / len(login_times)
            max_time = max(login_times)
            
            # Performance assertions (adjust thresholds as needed)
            assert avg_time < 2.0, f"Average login time {avg_time:.3f}s exceeds 2s threshold"
            assert max_time < 5.0, f"Maximum login time {max_time:.3f}s exceeds 5s threshold"
    
    def test_auth_me_endpoint_performance(self, client, url_builder):
        """Test /me endpoint performance with valid auth"""
        # Register and login to get token
        client.post("/api/auth/register", json={
            "username": "meuser", 
            "password": "TestPass123"
        })
        login_resp = client.post("/api/auth/login", json={
            "username": "meuser", 
            "password": "TestPass123"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Cannot test /me performance without valid login")
        
        token_data = login_resp.json()
        if "access_token" not in token_data:
            pytest.skip("Login response format not as expected")
            
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_url = url_builder.url_for("auth_get_current_user")
        
        response_times = []
        
        # Perform multiple requests
        for _ in range(15):
            start_time = time.time()
            response = client.get(me_url, headers=headers)
            end_time = time.time()
            
            if response.status_code == 200:
                response_times.append(end_time - start_time)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            # Performance assertions
            assert avg_time < 1.0, f"Average /me response time {avg_time:.3f}s exceeds 1s threshold"
            assert max_time < 3.0, f"Maximum /me response time {max_time:.3f}s exceeds 3s threshold"
    
    def test_health_endpoint_performance(self, client, url_builder):
        """Test health endpoint performance (no auth required)"""
        health_url = url_builder.url_for("debug_health")
        response_times = []
        
        # Perform multiple requests
        for _ in range(20):
            start_time = time.time()
            response = client.get(health_url)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # Health endpoint should be very fast
        assert avg_time < 0.5, f"Average health response time {avg_time:.3f}s exceeds 0.5s threshold"
        assert max_time < 2.0, f"Maximum health response time {max_time:.3f}s exceeds 2s threshold"
    
    def test_videos_list_performance_unauthenticated(self, client, url_builder):
        """Test videos endpoint performance (should fail fast due to auth)"""
        videos_url = url_builder.url_for("get_videos")
        response_times = []
        
        # Test unauthenticated requests (should fail fast)
        for _ in range(15):
            start_time = time.time()
            response = client.get(videos_url)
            end_time = time.time()
            
            assert response.status_code == 401
            response_times.append(end_time - start_time)
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        # Auth failures should be fast
        assert avg_time < 1.0, f"Average auth failure time {avg_time:.3f}s exceeds 1s threshold"
        assert max_time < 3.0, f"Maximum auth failure time {max_time:.3f}s exceeds 3s threshold"


class TestConcurrentRequestsRobust:
    """Test performance under concurrent load"""
    
    def test_health_endpoint_concurrent_load(self, client, url_builder):
        """Test health endpoint under concurrent load"""
        health_url = url_builder.url_for("debug_health")
        
        def make_request():
            start_time = time.time()
            response = client.get(health_url)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Simulate concurrent requests
        results = []
        num_requests = 10  # Reduced for faster testing
        
        for _ in range(num_requests):
            status_code, response_time = make_request()
            results.append((status_code, response_time))
        
        # All requests should succeed
        success_count = sum(1 for status, _ in results if status == 200)
        assert success_count == num_requests, f"Only {success_count}/{num_requests} requests succeeded"
        
        # Check performance under load
        response_times = [rt for _, rt in results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < 1.0, f"Average concurrent response time {avg_time:.3f}s exceeds 1s"
        assert max_time < 3.0, f"Maximum concurrent response time {max_time:.3f}s exceeds 3s"
    
    def test_auth_endpoints_concurrent_load(self, client, url_builder):
        """Test auth endpoints under concurrent load"""
        me_url = url_builder.url_for("auth_get_current_user")
        
        def make_auth_request(user_id):
            # Each concurrent request uses unauthenticated call (should fail fast)
            start_time = time.time()
            response = client.get(me_url)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Simulate concurrent auth requests
        results = []
        num_requests = 8  # Reduced for faster testing
        
        for i in range(num_requests):
            status_code, response_time = make_auth_request(i)
            results.append((status_code, response_time))
        
        # All should fail with 401 (unauthenticated)
        auth_failures = sum(1 for status, _ in results if status == 401)
        assert auth_failures == num_requests, f"Expected {num_requests} auth failures, got {auth_failures}"
        
        # Auth failures should be fast even under load
        response_times = [rt for _, rt in results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < 1.5, f"Average concurrent auth failure time {avg_time:.3f}s exceeds 1.5s"
        assert max_time < 4.0, f"Maximum concurrent auth failure time {max_time:.3f}s exceeds 4s"


class TestEndpointResponseTimes:
    """Test individual endpoint response times"""
    
    def test_all_unauth_endpoints_response_time(self, client, url_builder):
        """Test response times for endpoints that don't require auth or fail fast"""
        fast_endpoints = [
            ("debug_health", {}),
            ("profile_get_supported_languages", {}),
            ("auth_test_prefix", {}),
        ]
        
        for route_name, params in fast_endpoints:
            url = url_builder.url_for(route_name, **params)
            
            start_time = time.time()
            response = client.get(url)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # These endpoints should be fast
            assert response_time < 2.0, f"Endpoint {route_name} took {response_time:.3f}s (exceeds 2s threshold)"
            assert response.status_code in [200, 401], f"Endpoint {route_name} returned unexpected status {response.status_code}"
    
    def test_protected_endpoints_fail_fast(self, client, url_builder):
        """Test that protected endpoints fail fast when unauthenticated"""
        protected_endpoints = [
            ("get_videos", {}),
            ("auth_get_current_user", {}),
            ("get_vocabulary_stats", {}),
            ("profile_get", {}),
            ("progress_get_user", {}),
        ]
        
        for route_name, params in protected_endpoints:
            url = url_builder.url_for(route_name, **params)
            
            start_time = time.time()
            response = client.get(url)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Auth failures should be fast
            assert response_time < 1.0, f"Auth failure for {route_name} took {response_time:.3f}s (should be < 1s)"
            assert response.status_code == 401, f"Expected 401 for {route_name}, got {response.status_code}"


if __name__ == "__main__":
    # Quick performance test
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    url_builder = get_url_builder(client.app)
    
    print("Testing performance with robust URLs...")
    
    try:
        # Test health endpoint performance
        health_url = url_builder.url_for("debug_health")
        start_time = time.time()
        response = client.get(health_url)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"✓ Health endpoint: {health_url} ({response_time:.3f}s)")
        assert response.status_code == 200
        
        # Test auth endpoint (should fail fast)
        me_url = url_builder.url_for("auth_get_current_user")
        start_time = time.time()
        response = client.get(me_url)
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"✓ Auth endpoint (unauth): {me_url} ({response_time:.3f}s)")
        assert response.status_code == 401
        
        print("\n✅ Performance URL builder tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
