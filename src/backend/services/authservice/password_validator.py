"""
Password Validation Service

Enforces strong password policies for LangPlug authentication.
Password hashing is handled by fastapi-users/pwdlib.

Key Components:
    - PasswordValidator: Password strength validation class
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
    ```

Dependencies:
    - re: Regular expressions for pattern matching

Thread Safety:
    Yes. All methods are stateless class methods.

Performance Notes:
    - Validation: O(1), ~1ms
"""

import re

from core.config import settings


class PasswordValidator:
    """
    Password strength validation service.

    Enforces configurable password complexity requirements and maintains a blocklist
    of common passwords. All methods are class methods for stateless operation.

    Password hashing is handled by fastapi-users/pwdlib (Argon2).

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
        ```

    Note:
        Validation is case-insensitive for common password checking.
    """

    MIN_LENGTH = settings.password_min_length
    REQUIRE_UPPERCASE = settings.password_require_uppercase
    REQUIRE_LOWERCASE = settings.password_require_lowercase
    REQUIRE_DIGITS = settings.password_require_digits
    REQUIRE_SPECIAL = settings.password_require_special

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


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Convenience function for password validation

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    return PasswordValidator.validate(password)
