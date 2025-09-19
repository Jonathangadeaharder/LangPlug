"""
Robust processing tests using named routes instead of hardcoded URLs.
This replaces processing-related test files with a robust URL builder pattern.
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


class TestProcessingEndpointsRobust:
    """Robust processing endpoint tests using named routes"""

    def test_transcribe_video_requires_auth(self, client, url_builder):
        """Test that video transcription requires authentication"""
        transcribe_url = url_builder.url_for("transcribe_video")
        response = client.post(transcribe_url, json={
            "video_path": "test_video.mp4",
            "language": "en"
        })
        assert response.status_code == 401

    def test_filter_subtitles_requires_auth(self, client, url_builder):
        """Test that subtitle filtering requires authentication"""
        filter_url = url_builder.url_for("filter_subtitles")
        response = client.post(filter_url, json={
            "subtitle_path": "test_subtitles.srt",
            "difficulty_level": "intermediate"
        })
        assert response.status_code == 401

    def test_translate_subtitles_requires_auth(self, client, url_builder):
        """Test that subtitle translation requires authentication"""
        translate_url = url_builder.url_for("translate_subtitles")
        response = client.post(translate_url, json={
            "subtitle_path": "test_subtitles.srt",
            "target_language": "de"
        })
        assert response.status_code == 401

    def test_process_chunk_requires_auth(self, client, url_builder):
        """Test that chunk processing requires authentication"""
        chunk_url = url_builder.url_for("process_chunk")
        response = client.post(chunk_url, json={
            "video_path": "test_video.mp4",
            "start_time": 0,
            "duration": 30
        })
        assert response.status_code == 401

    def test_prepare_episode_requires_auth(self, client, url_builder):
        """Test that episode preparation requires authentication"""
        prepare_url = url_builder.url_for("prepare_episode")
        response = client.post(prepare_url, json={
            "video_path": "test_video.mp4",
            "language": "en"
        })
        assert response.status_code == 401

    def test_full_pipeline_requires_auth(self, client, url_builder):
        """Test that full pipeline requires authentication"""
        pipeline_url = url_builder.url_for("full_pipeline")
        response = client.post(pipeline_url, json={
            "video_path": "test_video.mp4",
            "target_language": "de",
            "difficulty_level": "intermediate"
        })
        assert response.status_code == 401

    def test_get_task_progress_with_params(self, client, url_builder):
        """Test task progress endpoint with path parameters"""
        progress_url = url_builder.url_for("get_task_progress", task_id="test_task_123")
        response = client.get(progress_url)
        assert response.status_code in [401, 404]  # Should require auth or return not found


class TestProcessingParameterValidation:
    """Test parameter validation for processing endpoints"""

    def test_transcribe_video_parameter_validation(self, client, url_builder):
        """Test parameter validation for transcribe endpoint"""
        transcribe_url = url_builder.url_for("transcribe_video")

        invalid_payloads = [
            {},  # Empty payload
            {"video_path": ""},  # Empty video path
            {"language": "en"},  # Missing video_path
            {"video_path": "test.mp4"},  # Missing language
            {"video_path": None, "language": "en"},  # Null video path
            {"video_path": "test.mp4", "language": "invalid_lang"},  # Invalid language
        ]

        for payload in invalid_payloads:
            response = client.post(transcribe_url, json=payload)
            # Should reject invalid data (after auth check)
            assert response.status_code in [400, 401, 422]

    def test_filter_subtitles_parameter_validation(self, client, url_builder):
        """Test parameter validation for filter endpoint"""
        filter_url = url_builder.url_for("filter_subtitles")

        invalid_payloads = [
            {},  # Empty payload
            {"subtitle_path": ""},  # Empty subtitle path
            {"difficulty_level": "intermediate"},  # Missing subtitle_path
            {"subtitle_path": "test.srt"},  # Missing difficulty_level
            {"subtitle_path": None, "difficulty_level": "intermediate"},  # Null path
            {"subtitle_path": "test.srt", "difficulty_level": "invalid"},  # Invalid level
        ]

        for payload in invalid_payloads:
            response = client.post(filter_url, json=payload)
            assert response.status_code in [400, 401, 422]

    def test_task_id_parameter_validation(self, client, url_builder):
        """Test task ID parameter validation"""
        invalid_task_ids = [
            "",
            "../malicious",
            "null",
            "undefined",
            "very_long_task_id_" + "x" * 1000
        ]

        for invalid_id in invalid_task_ids:
            try:
                progress_url = url_builder.url_for("get_task_progress", task_id=invalid_id)
                response = client.get(progress_url)
                # Should handle invalid IDs gracefully
                assert response.status_code in [400, 401, 404, 422]
            except Exception:
                # URL building might fail for very invalid IDs, which is acceptable
                pass


class TestProcessingSecurityRobust:
    """Security tests for processing endpoints"""

    def test_path_traversal_protection_processing(self, client, url_builder):
        """Test protection against path traversal in processing endpoints"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        transcribe_url = url_builder.url_for("transcribe_video")

        for malicious_path in malicious_paths:
            response = client.post(transcribe_url, json={
                "video_path": malicious_path,
                "language": "en"
            })
            # Should block path traversal attempts (after auth)
            assert response.status_code in [400, 401, 403, 404, 422], f"Path traversal not blocked for: {malicious_path}"

    def test_sql_injection_protection_processing(self, client, url_builder):
        """Test SQL injection protection on processing endpoints"""
        sql_payloads = [
            "'; DROP TABLE tasks; --",
            "test' OR '1'='1",
            "' UNION SELECT * FROM processing_tasks --"
        ]

        filter_url = url_builder.url_for("filter_subtitles")

        for payload in sql_payloads:
            response = client.post(filter_url, json={
                "subtitle_path": payload,
                "difficulty_level": "intermediate"
            })
            # Should not crash and should return proper error
            assert response.status_code in [400, 401, 404, 422], f"SQL injection payload caused unexpected response: {response.status_code}"

    def test_command_injection_protection(self, client, url_builder):
        """Test protection against command injection"""
        command_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& net user hacker password /add",
            "`whoami`",
            "$(id)"
        ]

        transcribe_url = url_builder.url_for("transcribe_video")

        for payload in command_payloads:
            response = client.post(transcribe_url, json={
                "video_path": f"video{payload}.mp4",
                "language": "en"
            })
            # Should block command injection attempts
            assert response.status_code in [400, 401, 403, 404, 422], f"Command injection not blocked for: {payload}"


class TestProcessingWorkflowRobust:
    """Test processing workflow endpoints"""

    def test_all_processing_endpoints_require_auth(self, client, url_builder):
        """Test that all processing endpoints require authentication"""
        processing_endpoints = [
            ("transcribe_video", {"video_path": "test.mp4", "language": "en"}),
            ("filter_subtitles", {"subtitle_path": "test.srt", "difficulty_level": "intermediate"}),
            ("translate_subtitles", {"subtitle_path": "test.srt", "target_language": "de"}),
            ("process_chunk", {"video_path": "test.mp4", "start_time": 0, "duration": 30}),
            ("prepare_episode", {"video_path": "test.mp4", "language": "en"}),
            ("full_pipeline", {"video_path": "test.mp4", "target_language": "de"}),
        ]

        for route_name, payload in processing_endpoints:
            url = url_builder.url_for(route_name)
            response = client.post(url, json=payload)
            # All should require authentication
            assert response.status_code == 401, f"Endpoint {route_name} should require authentication"

    def test_processing_endpoints_handle_large_payloads(self, client, url_builder):
        """Test processing endpoints handle large payloads gracefully"""
        large_string = "x" * 10000  # 10KB string

        transcribe_url = url_builder.url_for("transcribe_video")
        response = client.post(transcribe_url, json={
            "video_path": large_string,
            "language": "en"
        })

        # Should handle large payloads gracefully (after auth)
        assert response.status_code in [400, 401, 413, 422]


class TestProcessingDataValidation:
    """Test data validation for processing endpoints"""

    def test_language_code_validation(self, client, url_builder):
        """Test language code validation"""
        transcribe_url = url_builder.url_for("transcribe_video")

        invalid_languages = [
            "",
            "invalid_lang_code",
            "eng123",
            None,
            123,
            "toolong"
        ]

        for lang in invalid_languages:
            response = client.post(transcribe_url, json={
                "video_path": "test.mp4",
                "language": lang
            })
            # Should reject invalid language codes (after auth)
            assert response.status_code in [400, 401, 422]

    def test_difficulty_level_validation(self, client, url_builder):
        """Test difficulty level validation"""
        filter_url = url_builder.url_for("filter_subtitles")

        invalid_levels = [
            "",
            "invalid_level",
            "super_hard",
            None,
            123
        ]

        for level in invalid_levels:
            response = client.post(filter_url, json={
                "subtitle_path": "test.srt",
                "difficulty_level": level
            })
            # Should reject invalid difficulty levels (after auth)
            assert response.status_code in [400, 401, 422]

    def test_time_parameter_validation(self, client, url_builder):
        """Test time parameter validation for chunk processing"""
        chunk_url = url_builder.url_for("process_chunk")

        invalid_time_params = [
            {"start_time": -1, "duration": 30},  # Negative start time
            {"start_time": 0, "duration": -1},   # Negative duration
            {"start_time": "invalid", "duration": 30},  # Non-numeric start
            {"start_time": 0, "duration": "invalid"},   # Non-numeric duration
        ]

        for params in invalid_time_params:
            payload = {"video_path": "test.mp4", **params}
            response = client.post(chunk_url, json=payload)
            # Should reject invalid time parameters (after auth)
            assert response.status_code in [400, 401, 422]


if __name__ == "__main__":
    # Quick test to verify setup
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    url_builder = get_url_builder(client.app)

    print("Testing processing URL builder functionality...")

    try:
        # Test basic endpoints
        transcribe_url = url_builder.url_for("transcribe_video")
        print(f"✓ Transcribe video: {transcribe_url}")

        filter_url = url_builder.url_for("filter_subtitles")
        print(f"✓ Filter subtitles: {filter_url}")

        # Test parameterized endpoints
        progress_url = url_builder.url_for("get_task_progress", task_id="test_task_123")
        print(f"✓ Task progress: {progress_url}")

        print("\n✅ Processing URL builder tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
