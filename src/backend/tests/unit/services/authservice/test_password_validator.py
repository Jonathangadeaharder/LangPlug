"""
Unit tests for PasswordValidator

Tests password strength requirements, common password blocking, and hashing
"""

from services.authservice.password_validator import PasswordValidator


class TestPasswordValidation:
    """Test password strength validation rules"""

    def test_validate_minimum_length_too_short(self):
        """Passwords shorter than 8 characters should be rejected"""
        is_valid, error = PasswordValidator.validate("Short1!")
        assert is_valid is False
        assert "8 characters" in error

    def test_validate_minimum_length_exactly_8(self):
        """Password with exactly 8 characters should pass length check"""
        # This will fail other checks if they are enabled, but length is fine
        # Given we disabled uppercase/special, "a" * 8 might still fail digits/lowercase if enabled
        # Let's use a simple valid one: "password" (8 chars, lowercase)
        # But wait, common password check might block it.
        # Use "pass1234" (8 chars, lowercase + digits)
        password = "pass1234"
        _is_valid, error = PasswordValidator.validate(password)
        # Will fail for other reasons if any, but not length
        assert "8 characters" not in error

    def test_validate_requires_uppercase(self):
        """Password without uppercase should be rejected when uppercase is required"""
        # "lowercase123!" -> lowercase + digits + special but no uppercase
        # Default settings require uppercase
        is_valid, error = PasswordValidator.validate("lowercase123!")
        assert is_valid is False
        assert "uppercase" in error.lower()

    def test_validate_requires_lowercase(self):
        """Password without lowercase should be rejected"""
        # Assuming lowercase is still required
        is_valid, error = PasswordValidator.validate("UPPERCASE123!")
        assert is_valid is False
        assert "lowercase" in error.lower()

    def test_validate_requires_digit(self):
        """Password without digit should be rejected"""
        # Assuming digits are still required
        is_valid, error = PasswordValidator.validate("NoDigitsHere!")
        assert is_valid is False
        assert "digit" in error.lower()

    def test_validate_requires_special_character(self):
        """Password without special character should be rejected when special is required"""
        # "NoSpecial123" -> Mixed case + digits but no special character
        # Default settings require special character
        is_valid, error = PasswordValidator.validate("NoSpecial123")
        assert is_valid is False
        assert "special" in error.lower()

    def test_validate_strong_password_success(self):
        """Strong password meeting all requirements should pass"""
        is_valid, error = PasswordValidator.validate("SecurePass123!")
        assert is_valid is True
        assert error == ""

    def test_validate_various_special_characters(self):
        """Password with different special characters should pass"""
        special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "?"]
        for char in special_chars:
            password = f"SecurePass123{char}"
            is_valid, error = PasswordValidator.validate(password)
            assert is_valid is True, f"Failed with special char: {char}, error: {error}"


class TestCommonPasswordBlocking:
    """Test common password detection and blocking"""

    def test_validate_blocks_common_password_lowercase(self):
        """Common passwords should be blocked (case-insensitive)"""
        # "password1234" meets length (8+)
        is_valid, error = PasswordValidator.validate("Password1234!")
        assert is_valid is False
        assert "common" in error.lower()

    def test_validate_blocks_common_password_uppercase(self):
        """Common passwords should be blocked regardless of case"""
        # Case variation of password1234
        is_valid, error = PasswordValidator.validate("pASSWORD1234!")
        assert is_valid is False
        assert "common" in error.lower()

    def test_validate_blocks_common_password_mixed_case(self):
        """Common passwords with mixed case should be blocked"""
        # Mixed case variation
        is_valid, error = PasswordValidator.validate("PaSsWoRd1234!")
        assert is_valid is False
        assert "common" in error.lower()

    def test_validate_blocks_admin_password(self):
        """Admin variations should be blocked"""
        is_valid, error = PasswordValidator.validate("Admin1234567!")
        assert is_valid is False
        assert "common" in error.lower()

    def test_validate_blocks_welcome_password(self):
        """Welcome variations should be blocked"""
        is_valid, error = PasswordValidator.validate("Welcome1234!")
        assert is_valid is False
        assert "common" in error.lower()

    def test_validate_blocks_langplug_password(self):
        """Application-specific common passwords should be blocked"""
        is_valid, error = PasswordValidator.validate("Langplug123!")
        assert is_valid is False
        assert "common" in error.lower()

    def test_validate_allows_similar_to_common(self):
        """Passwords similar but not identical to common ones should pass"""
        # password123 is common, but SecurePassword123! is not
        is_valid, _error = PasswordValidator.validate("SecurePassword123!")
        assert is_valid is True


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_validate_exactly_minimum_length_with_all_requirements(self):
        """8-character password with requirements should pass"""
        is_valid, _error = PasswordValidator.validate("Secure1!")  # Exactly 8 chars
        assert is_valid is True

    def test_validate_very_long_password(self):
        """Very long password should be accepted"""
        long_password = "SecurePassword123!" * 10  # 180 characters
        is_valid, _error = PasswordValidator.validate(long_password)
        assert is_valid is True

    def test_validate_only_special_characters_with_requirements(self):
        """Password with multiple special characters should pass"""
        is_valid, _error = PasswordValidator.validate("S3cure!@#$%^Pass")
        assert is_valid is True

    def test_validate_unicode_characters(self):
        """Password with Unicode characters should be validated"""
        # Contains uppercase, lowercase, digit, special, and Unicode
        password = "SecurePass123!мир"
        is_valid, _error = PasswordValidator.validate(password)
        # Should pass validation (Unicode chars don't break rules)
        assert is_valid is True


class TestValidationReturnFormat:
    """Test validation return format consistency"""

    def test_validate_success_returns_tuple(self):
        """Successful validation should return (True, '')"""
        is_valid, error = PasswordValidator.validate("SecurePass123!")
        assert isinstance(is_valid, bool)
        assert isinstance(error, str)
        assert is_valid is True
        assert error == ""

    def test_validate_failure_returns_tuple(self):
        """Failed validation should return (False, error_message)"""
        is_valid, error = PasswordValidator.validate("short")
        assert isinstance(is_valid, bool)
        assert isinstance(error, str)
        assert is_valid is False
        assert len(error) > 0

    def test_validate_error_messages_are_descriptive(self):
        """Error messages should clearly describe the issue"""
        test_cases = [
            ("short", "8 characters"),
            # ("nouppercase123!", "uppercase"), # No longer required
            ("NOLOWERCASE123!", "lowercase"),
            ("NoDigitsHere!", "digit"),
            # ("NoSpecial123", "special"), # No longer required
            ("Password1234!", "common"),  # Meets complexity but is common
        ]

        for password, expected_keyword in test_cases:
            is_valid, error = PasswordValidator.validate(password)
            assert is_valid is False
            assert expected_keyword.lower() in error.lower(), f"Expected '{expected_keyword}' in error for '{password}'"
