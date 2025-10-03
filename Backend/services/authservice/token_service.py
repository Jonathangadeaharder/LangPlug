"""
JWT Token Service

Secure JWT token management implementing access/refresh token pattern for authentication.
This module provides stateless authentication using signed JSON Web Tokens with HMAC-SHA256.

Key Components:
    - TokenService: Main JWT token management class
    - Access tokens: Short-lived (1 hour) for API authentication
    - Refresh tokens: Long-lived (30 days) for token renewal
    - Token type validation to prevent token substitution attacks

Usage Example:
    ```python
    from services.authservice.token_service import TokenService

    # Create token pair for user
    tokens = TokenService.create_token_pair(user_id=123)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Verify access token
    user_id = TokenService.verify_access_token(access_token)

    # Refresh access token
    new_access = TokenService.refresh_access_token(refresh_token)
    ```

Dependencies:
    - jose: JWT encoding/decoding (python-jose library)
    - core.config: Secret key and settings
    - core.exceptions: Authentication error handling

Security Features:
    - HMAC-SHA256 signing algorithm
    - Token type validation (prevents using refresh token as access token)
    - Automatic expiration checking
    - Issued-at timestamp for audit trails

Thread Safety:
    Yes. All methods are stateless class methods with no shared mutable state.

Performance Notes:
    - Token creation: O(1), ~1ms
    - Token validation: O(1), ~1ms
    - No database queries required (stateless)
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from core.config import settings
from core.exceptions import AuthenticationError


class TokenService:
    """
    Stateless JWT token management service.

    Provides secure token creation, validation, and refresh functionality using JSON Web Tokens.
    All methods are class methods for stateless operation (no instance needed).

    Class Attributes:
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Access token lifetime (60 minutes)
        REFRESH_TOKEN_EXPIRE_DAYS (int): Refresh token lifetime (30 days)
        ALGORITHM (str): JWT signing algorithm (HS256)

    Token Payload Structure:
        Access Token:
            - sub: User ID (string)
            - exp: Expiration timestamp
            - iat: Issued-at timestamp
            - type: "access"

        Refresh Token:
            - sub: User ID (string)
            - exp: Expiration timestamp
            - iat: Issued-at timestamp
            - type: "refresh"

    Example:
        ```python
        # Create token pair
        tokens = TokenService.create_token_pair(user_id=42)

        # Verify access token
        try:
            user_id = TokenService.verify_access_token(tokens["access_token"])
        except AuthenticationError:
            # Token invalid/expired
            pass

        # Refresh access token
        new_access = TokenService.refresh_access_token(tokens["refresh_token"])
        ```

    Security Notes:
        - Never expose secret_key from settings
        - Token type field prevents substitution attacks
        - UTC timestamps prevent timezone manipulation
        - Refresh tokens should be stored securely (httpOnly cookies)
    """

    # Token configuration
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour (reduced from 24 hours)
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
    ALGORITHM = "HS256"

    @classmethod
    def create_access_token(cls, user_id: int, additional_claims: dict | None = None) -> str:
        """
        Create a short-lived access token for API authentication.

        Access tokens should be sent with each API request in the Authorization header.
        They expire after 1 hour for security.

        Args:
            user_id (int): User ID to encode in token subject (sub claim)
            additional_claims (dict | None): Optional extra claims to include in payload

        Returns:
            str: Encoded JWT access token string

        Example:
            ```python
            # Basic token
            token = TokenService.create_access_token(user_id=123)

            # With additional claims
            token = TokenService.create_access_token(
                user_id=123,
                additional_claims={"role": "admin", "permissions": ["read", "write"]}
            )
            ```

        Note:
            Token includes "type": "access" claim to prevent token substitution.
            Additional claims are merged into payload, overriding defaults if keys conflict.
        """
        expires = datetime.now(UTC) + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),
            "exp": expires,
            "iat": datetime.now(UTC),
            "type": "access",
        }

        # Add any additional claims
        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, settings.secret_key, algorithm=cls.ALGORITHM)

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        """
        Create a long-lived refresh token for obtaining new access tokens.

        Refresh tokens should be stored securely (httpOnly cookie) and used only to
        obtain new access tokens when they expire.

        Args:
            user_id (int): User ID to encode in token subject (sub claim)

        Returns:
            str: Encoded JWT refresh token string

        Example:
            ```python
            refresh_token = TokenService.create_refresh_token(user_id=123)
            # Store in httpOnly cookie
            response.set_cookie(
                "refresh_token",
                refresh_token,
                httponly=True,
                secure=True,
                samesite="strict"
            )
            ```

        Note:
            Refresh tokens last 30 days and include "type": "refresh" claim.
            They cannot be used as access tokens due to type validation.
        """
        expires = datetime.now(UTC) + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "exp": expires,
            "iat": datetime.now(UTC),
            "type": "refresh",
        }

        return jwt.encode(payload, settings.secret_key, algorithm=cls.ALGORITHM)

    @classmethod
    def create_token_pair(cls, user_id: int) -> dict[str, str]:
        """
        Create both access and refresh tokens

        Args:
            user_id: User ID

        Returns:
            Dictionary with access_token and refresh_token
        """
        return {
            "access_token": cls.create_access_token(user_id),
            "refresh_token": cls.create_refresh_token(user_id),
            "token_type": "bearer",
            "expires_in": cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        }

    @classmethod
    def decode_token(cls, token: str, expected_type: str | None = None) -> dict:
        """
        Decode and validate JWT token with optional type checking.

        Verifies token signature, expiration, and optionally validates token type to
        prevent token substitution attacks.

        Args:
            token (str): JWT token string to decode
            expected_type (str | None): Expected token type ("access" or "refresh"), None to skip check

        Returns:
            dict: Decoded token payload containing claims (sub, exp, iat, type, etc.)

        Raises:
            AuthenticationError: If token signature invalid, expired, or wrong type

        Example:
            ```python
            # Decode without type validation
            payload = TokenService.decode_token(token)
            user_id = int(payload["sub"])

            # Decode with type validation
            try:
                payload = TokenService.decode_token(token, expected_type="access")
            except AuthenticationError as e:
                print(f"Invalid token: {e}")
            ```

        Note:
            Automatically checks expiration (exp claim).
            Type mismatch raises AuthenticationError with descriptive message.
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[cls.ALGORITHM])

            # Validate token type if specified
            if expected_type and payload.get("type") != expected_type:
                raise AuthenticationError(
                    f"Invalid token type. Expected '{expected_type}', got '{payload.get('type')}'"
                )

            return payload

        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> str:
        """
        Exchange refresh token for new access token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Validate refresh token
        payload = cls.decode_token(refresh_token, expected_type="refresh")

        # Get user ID from payload
        user_id = int(payload.get("sub"))

        # Create new access token
        return cls.create_access_token(user_id)

    @classmethod
    def get_user_id_from_token(cls, token: str) -> int:
        """
        Extract user ID from token

        Args:
            token: JWT token (access or refresh)

        Returns:
            User ID

        Raises:
            AuthenticationError: If token is invalid
        """
        payload = cls.decode_token(token)
        return int(payload.get("sub"))

    @classmethod
    def verify_access_token(cls, token: str) -> int:
        """
        Verify access token and return user ID

        Args:
            token: Access token to verify

        Returns:
            User ID if valid

        Raises:
            AuthenticationError: If token is invalid or wrong type
        """
        payload = cls.decode_token(token, expected_type="access")
        return int(payload.get("sub"))

    @classmethod
    def is_token_expired(cls, token: str) -> bool:
        """
        Check if token is expired

        Args:
            token: JWT token to check

        Returns:
            True if expired, False otherwise
        """
        try:
            payload = cls.decode_token(token)
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC)
            return True
        except AuthenticationError:
            return True

    @classmethod
    def get_token_expiry(cls, token: str) -> datetime | None:
        """
        Get token expiration time

        Args:
            token: JWT token

        Returns:
            Expiration datetime or None if invalid
        """
        try:
            payload = cls.decode_token(token)
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=UTC)
            return None
        except AuthenticationError:
            return None


# Convenience functions for common operations


def create_tokens_for_user(user_id: int) -> dict[str, str]:
    """
    Create access and refresh tokens for user

    Args:
        user_id: User ID

    Returns:
        Dictionary with token pair
    """
    return TokenService.create_token_pair(user_id)


def verify_access_token(token: str) -> int:
    """
    Verify access token and get user ID

    Args:
        token: Access token

    Returns:
        User ID

    Raises:
        AuthenticationError: If invalid
    """
    return TokenService.verify_access_token(token)


def refresh_token(refresh_token: str) -> str:
    """
    Get new access token from refresh token

    Args:
        refresh_token: Refresh token

    Returns:
        New access token

    Raises:
        AuthenticationError: If invalid
    """
    return TokenService.refresh_access_token(refresh_token)
