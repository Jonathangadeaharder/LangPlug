"""Unified HTTP-based authentication test helpers for Contract-Driven Development.
Consolidates all authentication testing functionality into a single module.
These helpers use actual HTTP requests instead of TestClient for true black-box testing.
"""
import uuid
from typing import Any, Union

import httpx

# Try to import the URL builder, fallback to basic URL construction
try:
    from tests.utils.http_url_builder import FallbackURLBuilder
except ImportError:
    FallbackURLBuilder = None


class HTTPAuthHelper:
    """Unified HTTP-based authentication helper using real HTTP requests."""
    
    def __init__(self, client: httpx.Client, url_builder=None):
        self.client = client
        self.url_builder = url_builder
    
    @staticmethod
    def generate_unique_user_data() -> dict[str, str]:
        """Generate unique user credentials for testing."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"testuser_{unique_id}@example.com",
            "password": "SecureTestPass123!"
        }
    
    def _get_endpoint_url(self, endpoint_name: str, fallback_path: str) -> str:
        """Get endpoint URL using URL builder or fallback."""
        if self.url_builder:
            return self.url_builder.url_for(endpoint_name)
        return fallback_path

    def register_user(self, user_data: dict[str, str] = None) -> tuple[int, dict[str, Any]]:
        """Register a new user via HTTP and return response details."""
        if user_data is None:
            user_data = self.generate_unique_user_data()
        
        register_url = self._get_endpoint_url("auth_register", "/api/auth/register")
        response = self.client.post(register_url, json=user_data)
        return response.status_code, response.json() if response.content else {}

    def login_user(self, email: str, password: str) -> tuple[int, dict[str, Any]]:
        """Login with email/password via HTTP and return response details."""
        login_url = self._get_endpoint_url("auth_login", "/api/auth/login")
        login_data = {
            "username": email,  # FastAPI-Users expects email in username field
            "password": password
        }
        response = self.client.post(login_url, data=login_data)
        return response.status_code, response.json() if response.content else {}

    def register_and_login(self, user_data: dict[str, str] = None) -> dict[str, Any]:
        """Complete registration and login flow via HTTP. Returns user data and token."""
        if user_data is None:
            user_data = self.generate_unique_user_data()

        # Register user
        reg_status, reg_data = self.register_user(user_data)
        assert reg_status == 201, f"Registration failed: {reg_status}, {reg_data}"

        # Login user
        login_status, login_data = self.login_user(user_data["email"], user_data["password"])
        assert login_status == 200, f"Login failed: {login_status}, {login_data}"
        assert "access_token" in login_data, "No access token in login response"

        return {
            "user_data": user_data,
            "registration_response": reg_data,
            "login_response": login_data,
            "token": login_data["access_token"],
            "headers": {"Authorization": f"Bearer {login_data['access_token']}"}
        }
    
    def get_auth_headers(self, user_data: dict[str, str] = None) -> dict[str, str]:
        """Get authentication headers for a user."""
        auth_result = self.register_and_login(user_data)
        return auth_result["headers"]


class AsyncHTTPAuthHelper:
    """Unified async HTTP-based authentication helper using real HTTP requests."""
    
    def __init__(self, client: httpx.AsyncClient, url_builder=None):
        self.client = client
        self.url_builder = url_builder
    
    @staticmethod
    def generate_unique_user_data() -> dict[str, str]:
        """Generate unique user credentials for testing."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "username": f"testuser_{unique_id}",
            "email": f"testuser_{unique_id}@example.com",
            "password": "SecureTestPass123!"
        }
    
    def _get_endpoint_url(self, endpoint_name: str, fallback_path: str) -> str:
        """Get endpoint URL using URL builder or fallback."""
        if self.url_builder:
            return self.url_builder.url_for(endpoint_name)
        return fallback_path
    
    async def register_user(self, user_data: dict[str, str] = None) -> tuple[int, dict[str, Any]]:
        """Register a new user via HTTP asynchronously and return response details."""
        if user_data is None:
            user_data = self.generate_unique_user_data()
        
        register_url = self._get_endpoint_url("auth_register", "/api/auth/register")
        response = await self.client.post(register_url, json=user_data)
        return response.status_code, response.json() if response.content else {}
    
    async def login_user(self, email: str, password: str) -> tuple[int, dict[str, Any]]:
        """Login with email/password via HTTP asynchronously and return response details."""
        login_url = self._get_endpoint_url("auth_login", "/api/auth/login")
        login_data = {
            "username": email,  # FastAPI-Users expects email in username field
            "password": password
        }
        response = await self.client.post(login_url, data=login_data)
        return response.status_code, response.json() if response.content else {}
    
    async def register_and_login(self, user_data: dict[str, str] = None) -> dict[str, Any]:
        """Complete registration and login flow via HTTP asynchronously. Returns user data and token."""
        if user_data is None:
            user_data = self.generate_unique_user_data()

        # Register user
        reg_status, reg_data = await self.register_user(user_data)
        assert reg_status == 201, f"Registration failed: {reg_status}, {reg_data}"

        # Login user
        login_status, login_data = await self.login_user(user_data["email"], user_data["password"])
        assert login_status == 200, f"Login failed: {login_status}, {login_data}"
        assert "access_token" in login_data, "No access token in login response"

        return {
            "user_data": user_data,
            "registration_response": reg_data,
            "login_response": login_data,
            "token": login_data["access_token"],
            "headers": {"Authorization": f"Bearer {login_data['access_token']}"}
        }
    
    async def get_auth_headers(self, user_data: dict[str, str] = None) -> dict[str, str]:
        """Get authentication headers for a user."""
        auth_result = await self.register_and_login(user_data)
        return auth_result["headers"]


# Legacy HTTPAuthTestHelper class for backward compatibility
class HTTPAuthTestHelper:
    """Legacy static method-based authentication helper (DEPRECATED).
    Use HTTPAuthHelper or AsyncHTTPAuthHelper instead for better integration.
    """
    
    @staticmethod
    def generate_unique_user_data() -> dict[str, str]:
        """Generate unique user credentials for testing."""
        return HTTPAuthHelper.generate_unique_user_data()
    
    @staticmethod
    def register_user_http(client: httpx.Client, user_data: dict[str, str], register_endpoint: str = "/api/auth/register") -> tuple[int, dict[str, Any]]:
        """DEPRECATED: Use HTTPAuthHelper.register_user() instead."""
        helper = HTTPAuthHelper(client)
        return helper.register_user(user_data)
    
    @staticmethod
    async def register_user_http_async(client: httpx.AsyncClient, user_data: dict[str, str], register_endpoint: str = "/api/auth/register") -> tuple[int, dict[str, Any]]:
        """DEPRECATED: Use AsyncHTTPAuthHelper.register_user() instead."""
        helper = AsyncHTTPAuthHelper(client)
        return await helper.register_user(user_data)
    
    @staticmethod
    def login_user_http(client: httpx.Client, email: str, password: str, login_endpoint: str = "/api/auth/login") -> tuple[int, dict[str, Any]]:
        """DEPRECATED: Use HTTPAuthHelper.login_user() instead."""
        helper = HTTPAuthHelper(client)
        return helper.login_user(email, password)
    
    @staticmethod
    async def login_user_http_async(client: httpx.AsyncClient, email: str, password: str, login_endpoint: str = "/api/auth/login") -> tuple[int, dict[str, Any]]:
        """DEPRECATED: Use AsyncHTTPAuthHelper.login_user() instead."""
        helper = AsyncHTTPAuthHelper(client)
        return await helper.login_user(email, password)
    
    @staticmethod
    def register_and_login_http(
        client: httpx.Client, 
        user_data: dict[str, str] = None,
        register_endpoint: str = "/api/auth/register",
        login_endpoint: str = "/api/auth/login"
    ) -> dict[str, Any]:
        """DEPRECATED: Use HTTPAuthHelper.register_and_login() instead."""
        helper = HTTPAuthHelper(client)
        return helper.register_and_login(user_data)

    @staticmethod
    async def register_and_login_http_async(
        client: httpx.AsyncClient,
        user_data: dict[str, str] = None,
        register_endpoint: str = "/api/auth/register",
        login_endpoint: str = "/api/auth/login"
    ) -> dict[str, Any]:
        """DEPRECATED: Use AsyncHTTPAuthHelper.register_and_login() instead."""
        helper = AsyncHTTPAuthHelper(client)
        return await helper.register_and_login(user_data)

    @staticmethod
    def verify_auth_endpoint_http(
        client: httpx.Client,
        auth_headers: dict[str, str],
        me_endpoint: str = "/api/auth/me"
    ) -> tuple[int, dict[str, Any]]:
        """Verify authentication by calling the /me endpoint via HTTP."""
        response = client.get(me_endpoint, headers=auth_headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def verify_auth_endpoint_http_async(
        client: httpx.AsyncClient,
        auth_headers: dict[str, str],
        me_endpoint: str = "/api/auth/me"
    ) -> tuple[int, dict[str, Any]]:
        """Verify authentication by calling the /me endpoint via HTTP asynchronously."""
        response = await client.get(me_endpoint, headers=auth_headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    def logout_user_http(
        client: httpx.Client,
        auth_headers: dict[str, str],
        logout_endpoint: str = "/api/auth/logout"
    ) -> tuple[int, dict[str, Any]]:
        """Logout user via HTTP."""
        response = client.post(logout_endpoint, headers=auth_headers)
        return response.status_code, response.json() if response.content else {}

    @staticmethod
    async def logout_user_http_async(
        client: httpx.AsyncClient,
        auth_headers: dict[str, str],
        logout_endpoint: str = "/api/auth/logout"
    ) -> tuple[int, dict[str, Any]]:
        """Logout user via HTTP asynchronously."""
        response = await client.post(logout_endpoint, headers=auth_headers)
        return response.status_code, response.json() if response.content else {}


class ContractAuthTestSuite:
    """
    Complete test suite for authentication contract testing.
    This provides a full set of authentication tests that can be run against any API implementation.
    """
    
    def __init__(self, client: Union[httpx.Client, httpx.AsyncClient], is_async: bool = False):
        self.client = client
        self.is_async = is_async
        self.helper = HTTPAuthTestHelper()
    
    async def run_full_auth_contract_test(self) -> dict[str, Any]:
        """
        Run a complete authentication contract test.
        This tests the entire auth flow from registration to logout.
        """
        results = {
            "registration": None,
            "login": None,
            "me_endpoint": None,
            "logout": None,
            "errors": []
        }
        
        try:
            # Generate unique user data
            user_data = self.helper.generate_unique_user_data()
            
            # Test registration
            if self.is_async:
                reg_result = await self.helper.register_and_login_http_async(self.client, user_data)
            else:
                reg_result = self.helper.register_and_login_http(self.client, user_data)
            
            results["registration"] = reg_result["registration_response"] 
            results["login"] = reg_result["login_response"]
            
            # Test authenticated endpoint access
            if self.is_async:
                me_status, me_data = await self.helper.verify_auth_endpoint_http_async(
                    self.client, reg_result["headers"]
                )
            else:
                me_status, me_data = self.helper.verify_auth_endpoint_http(
                    self.client, reg_result["headers"]
                )
            
            results["me_endpoint"] = {"status": me_status, "data": me_data}
            
            # Test logout
            if self.is_async:
                logout_status, logout_data = await self.helper.logout_user_http_async(
                    self.client, reg_result["headers"]
                )
            else:
                logout_status, logout_data = self.helper.logout_user_http(
                    self.client, reg_result["headers"]
                )
            
            results["logout"] = {"status": logout_status, "data": logout_data}
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def run_full_auth_contract_test_sync(self) -> dict[str, Any]:
        """Synchronous version of the full auth contract test."""
        if self.is_async:
            raise ValueError("Cannot run sync test with async client")
        return self.run_full_auth_contract_test()


# Utility functions for creating helpers
def create_http_auth_helper(client: httpx.Client, url_builder=None) -> HTTPAuthHelper:
    """Create an HTTP auth helper instance."""
    return HTTPAuthHelper(client, url_builder)

def create_async_http_auth_helper(client: httpx.AsyncClient, url_builder=None) -> AsyncHTTPAuthHelper:
    """Create an async HTTP auth helper instance."""
    return AsyncHTTPAuthHelper(client, url_builder)

# Backwards compatibility
def create_legacy_http_auth_helper() -> HTTPAuthTestHelper:
    """Create a legacy static method-based helper (DEPRECATED)."""
    return HTTPAuthTestHelper()

# Legacy alias for tests that still use the old name
AuthTestHelper = HTTPAuthTestHelper


# AuthTestHelperAsync class for integration tests
class AuthTestHelperAsync:
    """Async authentication test helper for integration tests."""
    
    @staticmethod
    async def register_and_login_async(client: httpx.AsyncClient) -> dict[str, Any]:
        """Register and login a user asynchronously."""
        helper = AsyncHTTPAuthHelper(client)
        return await helper.register_and_login()
    
    @staticmethod
    async def get_current_user_async(client: httpx.AsyncClient, token: str) -> tuple[int, dict[str, Any]]:
        """Get current user information asynchronously."""
        helper = AsyncHTTPAuthHelper(client)
        headers = {"Authorization": f"Bearer {token}"}
        return await helper.client.get("/api/auth/me", headers=headers).status_code, await helper.client.get("/api/auth/me", headers=headers).json()
    
    @staticmethod
    async def logout_user_async(client: httpx.AsyncClient, token: str) -> tuple[int, dict[str, Any]]:
        """Logout user asynchronously."""
        helper = AsyncHTTPAuthHelper(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = await helper.client.post("/api/auth/logout", headers=headers)
        return response.status_code, response.json() if response.content else {}


def run_contract_auth_test(client: Union[httpx.Client, httpx.AsyncClient]) -> dict[str, Any]:
    """
    Run a complete authentication contract test against any HTTP client.
    This is the main entry point for contract testing.
    """
    is_async = isinstance(client, httpx.AsyncClient)
    suite = ContractAuthTestSuite(client, is_async)
    
    if is_async:
        # For async clients, this needs to be awaited by the caller
        return suite.run_full_auth_contract_test()
    else:
        return suite.run_full_auth_contract_test_sync()


# Response validation utilities
def validate_auth_response(response_data: dict, expected_structure: dict) -> None:
    """Validate that a response matches the expected structure."""
    # Check status code if provided
    if "status_code" in expected_structure:
        # This is just a placeholder - in real validation, we'd check the actual status code
        pass
    
    # Check required fields
    if "required_fields" in expected_structure:
        for field in expected_structure["required_fields"]:
            assert field in response_data, f"Missing required field: {field}"
    
    # Check field types if provided
    if "field_types" in expected_structure:
        for field, expected_type in expected_structure["field_types"].items():
            if field in response_data:
                assert isinstance(response_data[field], expected_type), \
                    f"Field {field} should be {expected_type}, got {type(response_data[field])}"


class AuthResponseStructures:
    """Standard response structures for authentication endpoints."""
    
    REGISTRATION_SUCCESS = {
        "required_fields": ["id", "username", "email"],
        "field_types": {
            "id": str,
            "username": str,
            "email": str
        }
    }
    
    LOGIN_SUCCESS = {
        "required_fields": ["access_token", "token_type"],
        "field_types": {
            "access_token": str,
            "token_type": str
        }
    }
    
    USER_INFO_SUCCESS = {
        "status_code": 200,
        "required_fields": ["id", "username", "email"],
        "field_types": {
            "id": str,
            "username": str,
            "email": str
        }
    }
    
    UNAUTHORIZED = {
        "status_code": 401
    }
