"""
Unit tests for FileSecurityValidator

Tests path traversal prevention, file validation, and secure upload handling
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.file_security import FileSecurityValidator


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Fixture to provide a temporary upload directory for tests"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    with patch.object(FileSecurityValidator, "ALLOWED_UPLOAD_DIR", upload_dir):
        yield upload_dir


class TestFileSecurityValidator:
    """Test file security validation and sanitization"""

    def test_validate_file_extension_allowed_video(self):
        """Valid video extensions should be allowed"""
        assert FileSecurityValidator.validate_file_extension("video.mp4") is True
        assert FileSecurityValidator.validate_file_extension("video.webm") is True
        assert FileSecurityValidator.validate_file_extension("video.mkv") is True

    def test_validate_file_extension_allowed_subtitle(self):
        """Valid subtitle extensions should be allowed"""
        assert FileSecurityValidator.validate_file_extension("subtitle.srt") is True
        assert FileSecurityValidator.validate_file_extension("subtitle.vtt") is True

    def test_validate_file_extension_case_insensitive(self):
        """Extension validation should be case-insensitive"""
        assert FileSecurityValidator.validate_file_extension("VIDEO.MP4") is True
        assert FileSecurityValidator.validate_file_extension("Video.SRT") is True

    def test_validate_file_extension_disallowed(self):
        """Disallowed extensions should be rejected"""
        assert FileSecurityValidator.validate_file_extension("script.exe") is False
        assert FileSecurityValidator.validate_file_extension("shell.sh") is False
        assert FileSecurityValidator.validate_file_extension("code.py") is False

    def test_validate_file_extension_no_extension(self):
        """Files without extensions should be rejected"""
        assert FileSecurityValidator.validate_file_extension("noextension") is False

    def test_sanitize_filename_removes_dangerous_chars(self):
        """Sanitize should remove path separators and null bytes"""
        result = FileSecurityValidator.sanitize_filename("../etc/passwd")
        assert "/" not in result
        assert ".." not in result

        result = FileSecurityValidator.sanitize_filename("file\\..\\test.txt")
        assert "\\" not in result
        assert ".." not in result

        result = FileSecurityValidator.sanitize_filename("file\x00.txt")
        assert "\x00" not in result

    def test_sanitize_filename_limits_length(self):
        """Sanitize should limit filename to 255 characters"""
        long_name = "a" * 300 + ".txt"
        result = FileSecurityValidator.sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_sanitize_filename_preserves_valid_chars(self):
        """Sanitize should preserve alphanumeric, dash, underscore, dot"""
        result = FileSecurityValidator.sanitize_filename("my-video_file.mp4")
        assert result == "my-video_file.mp4"

    @pytest.mark.asyncio
    async def test_validate_file_upload_missing_filename(self):
        """Upload validation should reject files without filename"""
        mock_file = Mock()
        mock_file.filename = None

        with pytest.raises(ValueError, match="No filename provided"):
            await FileSecurityValidator.validate_file_upload(mock_file)

    @pytest.mark.asyncio
    async def test_validate_file_upload_disallowed_extension(self):
        """Upload validation should reject disallowed file types"""
        mock_file = Mock()
        mock_file.filename = "malicious.exe"

        with pytest.raises(ValueError, match="File type not allowed"):
            await FileSecurityValidator.validate_file_upload(mock_file, {".mp4", ".srt"})

    @pytest.mark.asyncio
    async def test_validate_file_upload_empty_file(self, temp_upload_dir):
        """Upload validation should reject empty files"""
        mock_file = Mock()
        mock_file.filename = "video.mp4"
        mock_file.file = Mock()
        mock_file.file.seek = Mock()
        mock_file.file.tell = Mock(return_value=0)

        with pytest.raises(ValueError, match="File is empty"):
            await FileSecurityValidator.validate_file_upload(mock_file, {".mp4"})

    @pytest.mark.asyncio
    async def test_validate_file_upload_file_too_large(self, temp_upload_dir):
        """Upload validation should reject oversized files"""
        mock_file = Mock()
        mock_file.filename = "huge.mp4"
        mock_file.file = Mock()
        mock_file.file.seek = Mock()
        # Set size to 501 MB (exceeds 500 MB limit)
        mock_file.file.tell = Mock(return_value=501 * 1024 * 1024)

        with pytest.raises(ValueError, match="File too large"):
            await FileSecurityValidator.validate_file_upload(mock_file, {".mp4"})

    @pytest.mark.asyncio
    async def test_validate_file_upload_success(self, temp_upload_dir):
        """Upload validation should succeed for valid files"""
        mock_file = Mock()
        mock_file.filename = "video.mp4"
        mock_file.file = Mock()
        mock_file.file.seek = Mock()
        # 10 MB file
        mock_file.file.tell = Mock(return_value=10 * 1024 * 1024)

        result = await FileSecurityValidator.validate_file_upload(mock_file, {".mp4"})

        assert isinstance(result, Path)
        assert result.suffix == ".mp4"
        mock_file.file.seek.assert_called()

    def test_get_safe_upload_path_no_extension(self):
        """Safe upload path should reject files without extension"""
        with pytest.raises(ValueError, match="File has no extension"):
            FileSecurityValidator.get_safe_upload_path("noextension")

    def test_get_safe_upload_path_disallowed_extension(self):
        """Safe upload path should reject disallowed extensions"""
        with pytest.raises(ValueError, match="not allowed"):
            FileSecurityValidator.get_safe_upload_path("malware.exe")

    def test_get_safe_upload_path_generates_uuid(self, temp_upload_dir):
        """Safe upload path should generate UUID filename by default"""
        path1 = FileSecurityValidator.get_safe_upload_path("video.mp4")
        path2 = FileSecurityValidator.get_safe_upload_path("video.mp4")

        # Should generate different UUIDs
        assert path1 != path2
        assert path1.suffix == ".mp4"
        assert path2.suffix == ".mp4"

    def test_get_safe_upload_path_preserves_name(self, temp_upload_dir):
        """Safe upload path should preserve name when requested"""
        path = FileSecurityValidator.get_safe_upload_path("my_video.mp4", preserve_name=True)

        assert "my_video" in str(path)
        assert path.suffix == ".mp4"

    def test_get_safe_upload_path_sanitizes_preserved_name(self, temp_upload_dir):
        """Safe upload path should sanitize preserved names"""
        path = FileSecurityValidator.get_safe_upload_path("../etc/passwd.mp4", preserve_name=True)

        assert "../" not in str(path)
        assert "etc" in str(path) or "passwd" in str(path)
        assert path.suffix == ".mp4"


class TestPathTraversalPrevention:
    """Test path traversal attack prevention"""

    def test_validate_file_path_rejects_parent_directory_traversal(self):
        """Path validation should reject ../ traversal attempts"""
        with pytest.raises(ValueError, match="Path traversal"):
            FileSecurityValidator.validate_file_path("../etc/passwd")

    def test_validate_file_path_rejects_absolute_paths(self):
        """Path validation should reject absolute paths"""
        with pytest.raises(ValueError, match="Path traversal"):
            FileSecurityValidator.validate_file_path("/etc/passwd")

        with pytest.raises(ValueError, match="Path traversal"):
            FileSecurityValidator.validate_file_path("\\Windows\\System32")

    def test_validate_file_path_rejects_backslash_traversal(self):
        """Path validation should reject Windows-style traversal"""
        with pytest.raises(ValueError, match="Path traversal"):
            FileSecurityValidator.validate_file_path("..\\..\\etc\\passwd")


class TestSecurityEdgeCases:
    """Test edge cases and security corner cases"""

    def test_sanitize_filename_null_byte_injection(self):
        """Sanitize should handle null byte injection attempts"""
        result = FileSecurityValidator.sanitize_filename("file.txt\x00.exe")
        assert "\x00" not in result

    def test_sanitize_filename_unicode_normalization(self):
        """Sanitize should handle Unicode filename attacks"""
        # Test with Unicode characters that might be normalized
        result = FileSecurityValidator.sanitize_filename("file\u202e.txt")
        # Should remove right-to-left override character
        assert "\u202e" not in result

    def test_extension_double_extension_attack(self):
        """Extension validation should handle double extension attacks"""
        # file.pdf.exe should be rejected as .exe
        assert FileSecurityValidator.validate_file_extension("file.pdf.exe") is False
        # file.mp4.sh should be rejected as .sh (shell script not in allowed list)
        assert FileSecurityValidator.validate_file_extension("file.mp4.sh") is False
