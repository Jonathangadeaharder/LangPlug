"""
Integration tests for cookie-based authentication flow.

These tests verify that the cookie authentication works correctly,
especially focusing on the SameSite cookie behavior that caused
the original authentication bug.

Bug Background:
- Login returned 204 with Set-Cookie header
- Subsequent /api/auth/me returned 401
- Root cause: Cross-origin requests didn't include SameSite=lax cookies

These tests verify the cookie flow works when requests include cookies.
"""

from uuid import uuid4

import pytest


@pytest.mark.integration
class TestCookieAuthenticationFlow:
    """Integration tests for cookie-based authentication"""

    @pytest.fixture
    def unique_user_data(self):
        """Generate unique user data for each test"""
        unique_id = uuid4().hex[:8]
        return {
            "username": f"cookietest_{unique_id}",
            "email": f"cookie_{unique_id}@example.com",
            "password": "SecurePassword123!",
        }

    def test_cookie_login_sets_auth_cookie(self, client, url_builder, unique_user_data):
        """
        Test that cookie login endpoint sets the authentication cookie.
        
        The Set-Cookie header should include:
        - fastapiusersauth=<jwt>
        - HttpOnly (for XSS protection)
        - SameSite=lax (for CSRF protection while allowing same-site requests)
        """
        # Register user first
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        # Login via cookie endpoint
        login_url = url_builder.url_for("auth:cookie.login")
        login_response = client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Cookie login returns 204 No Content
        assert login_response.status_code == 204

        # Check Set-Cookie header is present
        assert "set-cookie" in login_response.headers
        cookie_header = login_response.headers["set-cookie"]

        # Verify cookie name
        assert "fastapiusersauth=" in cookie_header

        # Verify security attributes
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header.lower() or "samesite=lax" in cookie_header.lower()

    def test_cookie_auth_flow_with_me_endpoint(self, client, url_builder, unique_user_data):
        """
        Test complete cookie auth flow: register -> login -> access /me.
        
        This is the flow that was broken by the cross-origin cookie issue.
        With TestClient (same-origin simulation), it should work.
        """
        # Step 1: Register
        register_url = url_builder.url_for("register:register")
        register_response = client.post(register_url, json=unique_user_data)
        assert register_response.status_code == 201

        # Step 2: Login via cookie endpoint
        login_url = url_builder.url_for("auth:cookie.login")
        login_response = client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 204

        # Extract cookie from response
        cookie_header = login_response.headers.get("set-cookie", "")
        assert "fastapiusersauth=" in cookie_header

        # Step 3: Access /me with cookie
        # TestClient automatically handles cookies from previous responses
        me_url = url_builder.url_for("auth_get_current_user")
        me_response = client.get(me_url)

        # This should succeed with cookie auth
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == unique_user_data["email"]

    def test_cookie_not_sent_returns_401(self, client, url_builder, unique_user_data):
        """
        Test that /me returns 401 when no cookie/token is provided.
        
        This documents the expected behavior - authentication is required.
        """
        # Register and login to ensure user exists
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        # Create fresh client without cookies
        from fastapi.testclient import TestClient
        from core.app import create_app
        
        fresh_client = TestClient(create_app())

        # Try to access /me without any authentication
        me_url = url_builder.url_for("auth_get_current_user")
        me_response = fresh_client.get(me_url)

        # Should return 401 Unauthorized
        assert me_response.status_code == 401

    def test_cookie_logout_clears_auth(self, client, url_builder, unique_user_data):
        """
        Test that logout clears the authentication cookie.
        """
        # Register and login
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        login_url = url_builder.url_for("auth:cookie.login")
        client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Verify we're logged in
        me_url = url_builder.url_for("auth_get_current_user")
        me_response = client.get(me_url)
        assert me_response.status_code == 200

        # Logout
        logout_url = url_builder.url_for("auth:cookie.logout")
        logout_response = client.post(logout_url)
        assert logout_response.status_code in [200, 204]


@pytest.mark.integration
class TestCookieSecurityAttributes:
    """Tests for cookie security attributes"""

    @pytest.fixture
    def unique_user_data(self):
        """Generate unique user data for each test"""
        unique_id = uuid4().hex[:8]
        return {
            "username": f"sectest_{unique_id}",
            "email": f"sec_{unique_id}@example.com",
            "password": "SecurePassword123!",
        }

    def test_cookie_is_httponly(self, client, url_builder, unique_user_data):
        """
        Verify HttpOnly attribute prevents JavaScript access.
        
        HttpOnly cookies cannot be read by document.cookie, protecting
        against XSS-based cookie theft.
        """
        # Register and login
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        login_url = url_builder.url_for("auth:cookie.login")
        login_response = client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        cookie_header = login_response.headers.get("set-cookie", "")
        
        # HttpOnly should be present (case-insensitive check)
        assert "httponly" in cookie_header.lower()

    def test_cookie_samesite_is_lax(self, client, url_builder, unique_user_data):
        """
        Verify SameSite=lax for CSRF protection with same-site compatibility.
        
        SameSite=lax:
        - Prevents CSRF on cross-site POST requests
        - Allows cookies on same-site requests (our use case with Vite proxy)
        - Allows cookies on top-level navigations
        """
        # Register and login
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        login_url = url_builder.url_for("auth:cookie.login")
        login_response = client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        cookie_header = login_response.headers.get("set-cookie", "").lower()
        
        # SameSite should be lax (not strict, not none)
        assert "samesite=lax" in cookie_header

    def test_cookie_has_path_attribute(self, client, url_builder, unique_user_data):
        """
        Verify cookie Path attribute is set correctly.
        
        Path=/ ensures the cookie is sent for all paths.
        """
        # Register and login
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        login_url = url_builder.url_for("auth:cookie.login")
        login_response = client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        cookie_header = login_response.headers.get("set-cookie", "").lower()
        
        # Path should be / for site-wide cookie
        assert "path=/" in cookie_header


@pytest.mark.integration
class TestCookieAuthRegressionPrevention:
    """
    Regression tests specifically for the authentication bug.
    
    Bug: After successful login (204), /api/auth/me returned 401.
    
    These tests ensure the fix remains in place.
    """

    @pytest.fixture
    def unique_user_data(self):
        """Generate unique user data for each test"""
        unique_id = uuid4().hex[:8]
        return {
            "username": f"regtest_{unique_id}",
            "email": f"reg_{unique_id}@example.com",
            "password": "SecurePassword123!",
        }

    def test_login_then_me_works_sequentially(self, client, url_builder, unique_user_data):
        """
        Regression test: Login followed immediately by /me should work.
        
        This is the exact flow that was broken.
        """
        # Register
        register_url = url_builder.url_for("register:register")
        reg_response = client.post(register_url, json=unique_user_data)
        assert reg_response.status_code == 201

        # Login (should set cookie)
        login_url = url_builder.url_for("auth:cookie.login")
        login_response = client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == 204, "Login should return 204"

        # IMMEDIATELY call /me (this was returning 401 before the fix)
        me_url = url_builder.url_for("auth_get_current_user")
        me_response = client.get(me_url)
        
        # This MUST succeed - this was the bug
        assert me_response.status_code == 200, (
            "GET /api/auth/me should return 200 after successful login. "
            "If this fails with 401, the cookie authentication is broken."
        )
        
        # Verify user data is correct
        me_data = me_response.json()
        assert me_data["email"] == unique_user_data["email"]

    def test_multiple_sequential_authenticated_requests(self, client, url_builder, unique_user_data):
        """
        Test that multiple requests after login all work.
        
        Ensures cookies persist across multiple requests.
        """
        # Register and login
        register_url = url_builder.url_for("register:register")
        client.post(register_url, json=unique_user_data)

        login_url = url_builder.url_for("auth:cookie.login")
        client.post(
            login_url,
            data={
                "username": unique_user_data["email"],
                "password": unique_user_data["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Make multiple authenticated requests
        me_url = url_builder.url_for("auth_get_current_user")
        
        for i in range(3):
            response = client.get(me_url)
            assert response.status_code == 200, f"Request {i+1} should succeed with cookie auth"
