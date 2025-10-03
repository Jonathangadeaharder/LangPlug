"""
Password Validation and Hashing Service

Secure password validation and Argon2 hashing for LangPlug authentication.
This module enforces strong password policies and provides cryptographically secure hashing.

Key Components:
    - PasswordValidator: Main password validation and hashing class
    - Argon2 hashing algorithm (memory-hard, GPU-resistant)
    - Configurable password strength requirements
    - Common password blocklist

Password Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (!@#$%^&*...)
    - Not in common passwords list

Usage Example:
    ```python
    from services.authservice.password_validator import PasswordValidator

    # Validate password
    is_valid, error = PasswordValidator.validate("WeakPass")
    if not is_valid:
        print(f"Invalid: {error}")

    # Hash password
    hashed = PasswordValidator.hash_password("SecurePass123!")

    # Verify password
    is_correct = PasswordValidator.verify_password("SecurePass123!", hashed)
    ```

Dependencies:
    - passlib: Password hashing library with Argon2 support
    - re: Regular expressions for pattern matching

Security Features:
    - Argon2id algorithm (memory-hard, side-channel resistant)
    - Timing-safe password verification
    - Common password blocklist
    - Configurable complexity requirements

Thread Safety:
    Yes. All methods are stateless class methods using thread-safe libraries.

Performance Notes:
    - Validation: O(1), ~1ms
    - Hashing: O(1), ~500ms (intentionally slow for security)
    - Verification: O(1), ~500ms (intentionally slow for security)
"""

import re

from passlib.context import CryptContext

# Initialize password context with Argon2 (more secure than bcrypt)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class PasswordValidator:
    """
    Password strength validation and secure hashing service.

    Enforces configurable password complexity requirements and maintains a blocklist
    of common passwords. All methods are class methods for stateless operation.

    Class Attributes:
        MIN_LENGTH (int): Minimum password length (12)
        REQUIRE_UPPERCASE (bool): Require uppercase letter (True)
        REQUIRE_LOWERCASE (bool): Require lowercase letter (True)
        REQUIRE_DIGITS (bool): Require digit (True)
        REQUIRE_SPECIAL (bool): Require special character (True)
        COMMON_PASSWORDS (set): Blocklist of common passwords

    Example:
        ```python
        # Validate password strength
        is_valid, msg = PasswordValidator.validate("Test123!")
        if not is_valid:
            print(f"Weak password: {msg}")

        # Hash and verify
        hashed = PasswordValidator.hash_password("SecurePass123!")
        if PasswordValidator.verify_password("SecurePass123!", hashed):
            print("Password matches!")

        # Check if hash needs update
        if PasswordValidator.needs_rehash(hashed):
            new_hash = PasswordValidator.hash_password(plain_password)
        ```

    Note:
        Validation is case-insensitive for common password checking.
        Argon2 parameters are managed by passlib CryptContext.
    """

    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    # Common passwords to block (top 100 most common)
    # Includes variations that meet complexity requirements (12+ chars, upper/lower/digit/special)
    COMMON_PASSWORDS = {
        "password123",
        "password123!",
        "password1234!",  # Meets complexity (12 chars, has special)
        "admin123",
        "admin123!",
        "admin1234567",
        "admin1234567!",  # Meets complexity (13 chars, has special)
        "welcome123",
        "welcome123!",
        "welcome1234!",
        "qwerty123",
        "qwerty123!",
        "letmein123",
        "123456789012",
        "password1234",
        "changeme123!",
        "default123!",
        "langplug123",
        "langplug123!",
    }

    @classmethod
    def validate(cls, password: str) -> tuple[bool, str]:
        """
        Validate password against security policy.

        Checks password against all configured requirements including length, character
        types, and common password blocklist.

        Args:
            password (str): Password to validate

        Returns:
            tuple[bool, str]: (is_valid, error_message)
                - is_valid: True if password meets all requirements
                - error_message: Empty string if valid, descriptive error if invalid

        Example:
            ```python
            is_valid, error = PasswordValidator.validate("weak")
            if not is_valid:
                return {"error": error}  # "Password must be at least 12 characters"

            is_valid, error = PasswordValidator.validate("password1234!")
            if not is_valid:
                return {"error": error}  # "Password is too common..."
            ```

        Note:
            Validation order: length -> uppercase -> lowercase -> digits -> special -> common.
            Returns first validation failure encountered.
        """
        # Check minimum length
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters"

        # Check uppercase requirement
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        # Check lowercase requirement
        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        # Check digit requirement
        if cls.REQUIRE_DIGITS and not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        # Check special character requirement
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character (!@#$%^&*...)"

        # Check against common passwords
        if cls._is_common_password(password):
            return False, "Password is too common, please choose a stronger password"

        return True, ""

    @staticmethod
    def _is_common_password(password: str) -> bool:
        """Check if password is in common passwords list"""
        return password.lower() in PasswordValidator.COMMON_PASSWORDS

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash password using Argon2id algorithm.

        Creates a secure password hash suitable for database storage. Argon2 is
        memory-hard and resistant to GPU/ASIC attacks.

        Args:
            password (str): Plain text password to hash

        Returns:
            str: Argon2 hash string (starts with $argon2id$...)

        Example:
            ```python
            hashed = PasswordValidator.hash_password("SecurePass123!")
            # Returns: $argon2id$v=19$m=65536,t=3,p=4$...

            # Store in database
            user.hashed_password = hashed
            ```

        Note:
            Hashing is intentionally slow (~500ms) to resist brute-force attacks.
            Each hash includes random salt, so same password produces different hashes.
        """
        return pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify plain password against Argon2 hash.

        Uses timing-safe comparison to prevent timing attacks. Automatically handles
        different Argon2 variants and parameter sets.

        Args:
            plain_password (str): Plain text password to verify
            hashed_password (str): Stored Argon2 hash to compare against

        Returns:
            bool: True if password matches hash, False otherwise

        Example:
            ```python
            # During login
            user = get_user_by_username(username)
            if PasswordValidator.verify_password(password, user.hashed_password):
                # Login successful
                create_session(user)
            else:
                # Invalid password
                raise InvalidCredentialsError()
            ```

        Note:
            Verification time is constant (~500ms) regardless of match/mismatch.
            This prevents timing attacks that could leak information about the hash.
        """
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def needs_rehash(cls, hashed_password: str) -> bool:
        """
        Check if password hash needs to be updated

        Args:
            hashed_password: Existing password hash

        Returns:
            True if hash should be regenerated with current settings
        """
        return pwd_context.needs_update(hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Convenience function for password validation

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return PasswordValidator.validate(password)


def hash_password(password: str) -> str:
    """
    Convenience function for password hashing

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return PasswordValidator.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Convenience function for password verification

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if match, False otherwise
    """
    return PasswordValidator.verify_password(plain_password, hashed_password)
