"""
Fast authentication fixtures for testing.
Replaces slow bcrypt operations with instant mocks.
"""

import random
import uuid
from unittest.mock import patch

import pytest
from passlib.context import CryptContext

# Pre-hashed password for testing (actual bcrypt hash of "TestPassword123!")
FAST_PASSWORD_HASH = "$2b$12$8K1p/yXt5b0eMHXQ4qzKNOJ6QzVZG9C5F8YqRlhDmZq3Dv4tFzRuy"


class FastCryptContext:
    """Mock crypto context that returns instant results"""

    def hash(self, password: str) -> str:
        """Return fast mock hash with salt simulation"""
        salt = random.randint(100000, 999999)
        return f"$fast_hash${salt}${hash(password + str(salt))}"

    def verify(self, password: str, hash_value: str) -> bool:
        """Verify password against mock or real hash"""
        if hash_value.startswith("$fast_hash$"):
            # Extract salt from hash: $fast_hash$SALT$HASH
            parts = hash_value.split("$")
            if len(parts) >= 4:
                salt = parts[2]
                expected_hash = f"$fast_hash${salt}${hash(password + salt)}"
                return hash_value == expected_hash
            # Legacy format without salt
            return hash_value == f"$fast_hash${hash(password)}"
        # For real bcrypt hashes, use real verification (for backward compatibility)
        real_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return real_context.verify(password, hash_value)


@pytest.fixture(autouse=True)
def fast_passwords():
    """Replace password hashing/verification with instant mocks"""

    def fast_hash(password: str) -> str:
        """Fast hash with salt simulation"""
        salt = random.randint(100000, 999999)
        return f"$fast_hash${salt}${hash(password + str(salt))}"

    def fast_verify(password: str, hashed: str) -> bool:
        """Fast verification for our mock hashes and real bcrypt hashes"""
        if hashed.startswith("$fast_hash$"):
            # Handle both new salted format and legacy format
            parts = hashed.split("$")
            if len(parts) >= 4:
                # New format: $fast_hash$SALT$HASH
                salt = parts[2]
                expected_hash = f"$fast_hash${salt}${hash(password + salt)}"
                return hashed == expected_hash
            else:
                # Legacy format: $fast_hash$HASH
                return hashed == f"$fast_hash${hash(password)}"
        # For real bcrypt hashes, use real verification (backward compatibility)
        try:
            from passlib.context import CryptContext

            real_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return real_context.verify(password, hashed)
        except:
            return False

    # Patch FastAPI-Users PasswordHelper methods directly
    with patch("fastapi_users.password.PasswordHelper.hash") as mock_hash:
        with patch("fastapi_users.password.PasswordHelper.verify_and_update") as mock_verify:
            mock_hash.side_effect = fast_hash

            # verify_and_update returns (is_valid, updated_password_hash) tuple
            def fast_verify_and_update(password: str, hashed: str):
                is_valid = fast_verify(password, hashed)
                return is_valid, None  # No update needed for our fast hashes

            mock_verify.side_effect = fast_verify_and_update

            # Also patch any direct service imports
            with patch("services.authservice.auth_service.CryptContext") as mock_auth_crypto:
                fast_context = FastCryptContext()
                mock_auth_crypto.return_value = fast_context

                yield


@pytest.fixture
def fast_user_data():
    """Generate unique user data with fast hash"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"fastuser_{unique_id}",
        "email": f"fastuser_{unique_id}@example.com",
        "password": "TestPassword123!",
        "hashed_password": f"$fast_hash${hash('TestPassword123!')}",
    }


@pytest.fixture
async def fast_authenticated_user(async_client, fast_user_data):
    """Create and authenticate user quickly"""
    # Register user
    register_data = {
        "username": fast_user_data["username"],
        "email": fast_user_data["email"],
        "password": fast_user_data["password"],
    }

    register_response = await async_client.post("/api/auth/register", json=register_data)
    assert register_response.status_code == 201

    # Login user
    login_data = {"username": fast_user_data["email"], "password": fast_user_data["password"]}

    login_response = await async_client.post("/api/auth/login", data=login_data)
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return {"user_data": fast_user_data, "token": token, "headers": headers}
