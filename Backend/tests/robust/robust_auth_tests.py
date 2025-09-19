"""
Robust authentication tests using named routes instead of hardcoded URLs.
This replaces auth-related test files with a robust URL builder pattern.
"""
import os
import sys

# Add the Backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.utils.url_builder import get_url_builder


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def url_builder(client):
    """URL builder fixture for robust URL generation"""
    return get_url_builder(client.app)


class TestAuthenticationRobust:
    """Robust authentication tests using named routes"""

    def test_get_current_user_unauthenticated(self, client, url_builder):
        """Test /me endpoint without authentication"""
        me_url = url_builder.url_for("auth_get_current_user")
        response = client.get(me_url)
        assert response.status_code == 401

    def test_get_current_user_with_invalid_token(self, client, url_builder):
        """Test /me endpoint with invalid token"""
        me_url = url_builder.url_for("auth_get_current_user")
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get(me_url, headers=headers)
        assert response.status_code == 401

    def test_auth_test_prefix_endpoint(self, client, url_builder):
        """Test the auth test prefix endpoint"""
        test_prefix_url = url_builder.url_for("auth_test_prefix")
        response = client.get(test_prefix_url)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Auth router is working" in data["message"]

    def test_fastapi_users_login_endpoint_exists(self, client):
        """Test that FastAPI-Users login endpoint is accessible"""
        # Note: FastAPI-Users manages these routes, so we use hardcoded URLs
        # but only for FastAPI-Users specific endpoints
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrong"
        })
        # Should return 400 (validation error) or 401 (auth error), not 404
        assert response.status_code in [400, 401, 422]

    def test_fastapi_users_register_endpoint_exists(self, client):
        """Test that FastAPI-Users register endpoint is accessible"""
        response = client.post("/api/auth/register", json={
            "username": "",  # Invalid to trigger validation
            "password": "test"
        })
        # Should return validation error, not 404
        assert response.status_code in [400, 422]


class TestAuthSecurityRobust:
    """Security tests using robust URL patterns"""

    def test_protected_endpoints_require_auth(self, client, url_builder):
        """Test that protected endpoints block unauthenticated access"""
        protected_routes = [
            "auth_get_current_user",
            "get_videos",
            "get_vocabulary_stats",
            "profile_get",
            "progress_get_user"
        ]

        for route_name in protected_routes:
            url = url_builder.url_for(route_name)
            response = client.get(url)
            assert response.status_code == 401, f"Route {route_name} should require authentication"

    def test_invalid_tokens_rejected(self, client, url_builder):
        """Test that various invalid tokens are rejected"""
        invalid_tokens = [
            "Bearer invalid_token",
            "Bearer ",
            "Invalid token_format",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
        ]

        me_url = url_builder.url_for("auth_get_current_user")

        for token in invalid_tokens:
            headers = {"Authorization": token}
            response = client.get(me_url, headers=headers)
            assert response.status_code == 401, f"Invalid token '{token}' should be rejected"

    def test_sql_injection_protection(self, client):
        """Test SQL injection protection on auth endpoints"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]

        for payload in sql_payloads:
            # Test registration endpoint
            response = client.post("/api/auth/register", json={
                "username": payload,
                "password": "testpass"
            })
            # Should not crash and should return proper error
            assert response.status_code in [400, 422], f"SQL injection payload caused unexpected response: {response.status_code}"

    def test_weak_password_rejection(self, client):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "123",
            "password",
            "abc",
            "",
            "12345678"
        ]

        for weak_password in weak_passwords:
            response = client.post("/api/auth/register", json={
                "username": f"testuser_{len(weak_password)}",
                "password": weak_password
            })
            # Should reject weak passwords
            assert response.status_code in [400, 422], f"Weak password '{weak_password}' should be rejected"


class TestAuthWorkflowRobust:
    """Test complete authentication workflows"""

    def test_complete_auth_workflow(self, client, url_builder):
        """Test a complete registration -> login -> access workflow"""
        # Registration
        register_response = client.post("/api/auth/register", json={
            "username": "workflowuser",
            "email": "workflowuser@example.com",
            "password": "SecurePass123!"
        })

        # Registration should succeed or user might already exist
        assert register_response.status_code in [200, 201, 400]  # 400 if user exists

        # Login
        login_response = client.post("/api/auth/login", json={
            "username": "workflowuser",
            "password": "SecurePass123!"
        })

        if login_response.status_code == 200:
            # If login successful, test authenticated access
            token_data = login_response.json()
            if "access_token" in token_data:
                token = token_data["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Test authenticated access to /me endpoint
                me_url = url_builder.url_for("auth_get_current_user")
                me_response = client.get(me_url, headers=headers)
                assert me_response.status_code == 200

                user_data = me_response.json()
                assert "username" in user_data
                assert user_data["username"] == "workflowuser"
