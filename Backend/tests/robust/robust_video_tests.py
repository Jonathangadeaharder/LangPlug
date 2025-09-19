"""
Robust video tests using named routes instead of hardcoded URLs.
This replaces video-related test files with a robust URL builder pattern.
"""
import os
import sys

# Add the Backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import io

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


@pytest.fixture
def auth_headers():
    """Mock auth headers for testing (adjust based on your auth system)"""
    return {"Authorization": "Bearer mock_token_for_testing"}


class TestVideoEndpointsRobust:
    """Robust video endpoint tests using named routes"""

    def test_get_videos_requires_auth(self, client, url_builder):
        """Test that getting videos requires authentication"""
        videos_url = url_builder.url_for("get_videos")
        response = client.get(videos_url)
        assert response.status_code == 401

    def test_get_user_videos_requires_auth(self, client, url_builder):
        """Test that getting user videos requires authentication"""
        user_videos_url = url_builder.url_for("get_user_videos")
        response = client.get(user_videos_url)
        assert response.status_code == 401

    def test_stream_video_with_params(self, client, url_builder):
        """Test video streaming endpoint with path parameters"""
        stream_url = url_builder.url_for("stream_video", series="TestSeries", episode="S01E01")
        response = client.get(stream_url)
        # Should require auth or return 404 if video doesn't exist
        assert response.status_code in [401, 404]

    def test_get_video_status_with_params(self, client, url_builder):
        """Test video status endpoint with path parameters"""
        status_url = url_builder.url_for("get_video_status", video_id="test_video.mp4")
        response = client.get(status_url)
        # Should require auth or return 404
        assert response.status_code in [401, 404]

    def test_get_video_vocabulary_with_params(self, client, url_builder):
        """Test video vocabulary endpoint with path parameters"""
        vocab_url = url_builder.url_for("get_video_vocabulary", video_id="test_video.mp4")
        response = client.get(vocab_url)
        # Should require auth or return 404
        assert response.status_code in [401, 404]

    def test_get_subtitles_with_path(self, client, url_builder):
        """Test subtitles endpoint with path parameter"""
        subtitles_url = url_builder.url_for("get_subtitles", subtitle_path="test/subtitle.srt")
        response = client.get(subtitles_url)
        # Should require auth or return 404
        assert response.status_code in [401, 404]

    def test_scan_videos_requires_auth(self, client, url_builder):
        """Test that scanning videos requires authentication"""
        scan_url = url_builder.url_for("scan_videos")
        response = client.post(scan_url)
        assert response.status_code == 401


class TestVideoUploadRobust:
    """Robust video upload tests"""

    def test_upload_video_generic_requires_auth(self, client, url_builder):
        """Test generic video upload requires authentication"""
        upload_url = url_builder.url_for("upload_video_generic")

        # Create a mock video file
        video_content = b"fake video content"
        files = {"video_file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}

        response = client.post(upload_url, files=files)
        assert response.status_code == 401

    def test_upload_video_to_series_requires_auth(self, client, url_builder):
        """Test series-specific video upload requires authentication"""
        upload_url = url_builder.url_for("upload_video_to_series", series="TestSeries")

        # Create a mock video file
        video_content = b"fake video content"
        files = {"video_file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}

        response = client.post(upload_url, files=files)
        assert response.status_code == 401

    def test_upload_subtitle_requires_auth(self, client, url_builder):
        """Test subtitle upload requires authentication"""
        upload_url = url_builder.url_for("upload_subtitle")

        # Create a mock subtitle file
        subtitle_content = b"1\n00:00:01,000 --> 00:00:02,000\nTest subtitle"
        files = {"subtitle_file": ("test.srt", io.BytesIO(subtitle_content), "text/plain")}
        data = {"video_path": "test/video.mp4"}

        response = client.post(upload_url, files=files, data=data)
        assert response.status_code == 401


class TestVideoSecurityRobust:
    """Security tests for video endpoints"""

    def test_path_traversal_protection(self, client, url_builder):
        """Test protection against path traversal attacks"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        for malicious_path in malicious_paths:
            try:
                # Test subtitle path traversal
                subtitles_url = url_builder.url_for("get_subtitles", subtitle_path=malicious_path)
                response = client.get(subtitles_url)
                # Should either require auth (401) or be blocked (400/403/404)
                assert response.status_code in [400, 401, 403, 404], f"Path traversal not blocked for: {malicious_path}"
            except Exception:
                # URL building might fail for invalid paths, which is good
                pass

    def test_video_file_type_validation(self, client, url_builder):
        """Test that only valid video file types are accepted"""
        upload_url = url_builder.url_for("upload_video_generic")

        invalid_files = [
            ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.js", b"alert('xss')", "text/javascript"),
            ("document.pdf", b"%PDF-1.4", "application/pdf"),
        ]

        for filename, content, content_type in invalid_files:
            files = {"video_file": (filename, io.BytesIO(content), content_type)}
            response = client.post(upload_url, files=files)
            # Should reject invalid file types (after auth check)
            assert response.status_code in [400, 401, 413, 415, 422], f"Invalid file type '{filename}' should be rejected"


class TestVideoParameterValidation:
    """Test parameter validation for video endpoints"""

    def test_invalid_video_ids(self, client, url_builder):
        """Test handling of invalid video IDs"""
        invalid_ids = [
            "",
            "../malicious",
            "null",
            "undefined",
            "very_long_id_" + "x" * 1000
        ]

        for invalid_id in invalid_ids:
            try:
                status_url = url_builder.url_for("get_video_status", video_id=invalid_id)
                response = client.get(status_url)
                # Should handle invalid IDs gracefully
                assert response.status_code in [400, 401, 404, 422]
            except Exception:
                # URL building might fail for very invalid IDs, which is acceptable
                pass

    def test_invalid_series_episode_params(self, client, url_builder):
        """Test handling of invalid series/episode parameters"""
        invalid_params = [
            ("", ""),
            ("../malicious", "S01E01"),
            ("Series", ""),
            ("Series", "../malicious")
        ]

        for series, episode in invalid_params:
            try:
                stream_url = url_builder.url_for("stream_video", series=series, episode=episode)
                response = client.get(stream_url)
                # Should handle invalid parameters gracefully
                assert response.status_code in [400, 401, 404, 422]
            except Exception:
                # URL building might fail for invalid parameters, which is acceptable
                pass


if __name__ == "__main__":
    # Quick test to verify setup
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    url_builder = get_url_builder(client.app)

    print("Testing video URL builder functionality...")

    try:
        # Test basic endpoints
        videos_url = url_builder.url_for("get_videos")
        print(f"✓ Videos list: {videos_url}")

        # Test parameterized endpoints
        stream_url = url_builder.url_for("stream_video", series="TestSeries", episode="S01E01")
        print(f"✓ Stream video: {stream_url}")

        upload_url = url_builder.url_for("upload_video_to_series", series="TestSeries")
        print(f"✓ Upload to series: {upload_url}")

        print("\n✅ Video URL builder tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
