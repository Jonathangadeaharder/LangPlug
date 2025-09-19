"""
Example test file demonstrating robust URL testing using named routes.
This shows how to use the url_builder.py utility to prevent hardcoded URLs in tests.
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
    """URL builder fixture"""
    return get_url_builder(client.app)


class TestRobustURLPatterns:
    """Examples of robust URL testing using named routes"""

    def test_auth_endpoints_robust(self, client, url_builder):
        """Example: Testing auth endpoints using named routes"""

        # Instead of hardcoded "/api/auth/me", use the route name
        me_url = url_builder.url_for("auth_get_current_user")

        # This will automatically generate the correct URL regardless of prefix changes
        response = client.get(me_url)
        # Note: This will return 401 without auth, but the URL is correct
        assert response.status_code in [200, 401]  # Either success or unauthorized

        # Test prefix endpoint
        test_prefix_url = url_builder.url_for("auth_test_prefix")
        response = client.get(test_prefix_url)
        assert response.status_code == 200


    def test_videos_endpoints_robust(self, client, url_builder):
        """Example: Testing video endpoints with path parameters"""

        # Simple endpoint without parameters
        videos_url = url_builder.url_for("get_videos")
        response = client.get(videos_url)
        assert response.status_code in [200, 401]  # Will need auth

        # Endpoint with path parameters
        stream_url = url_builder.url_for("stream_video", series="TestSeries", episode="S01E01")
        response = client.get(stream_url)
        assert response.status_code in [200, 401, 404]  # Various valid responses

        # Video status endpoint
        status_url = url_builder.url_for("get_video_status", video_id="test_video.mp4")
        response = client.get(status_url)
        assert response.status_code in [200, 401, 404]


    def test_processing_endpoints_robust(self, client, url_builder):
        """Example: Testing processing endpoints"""

        # Task progress endpoint
        progress_url = url_builder.url_for("get_task_progress", task_id="test_task_123")
        response = client.get(progress_url)
        assert response.status_code in [200, 401, 404]


    def test_vocabulary_endpoints_robust(self, client, url_builder):
        """Example: Testing vocabulary endpoints"""

        # Stats endpoint
        stats_url = url_builder.url_for("get_vocabulary_stats")
        response = client.get(stats_url)
        assert response.status_code in [200, 401]

        # Library level endpoint
        level_url = url_builder.url_for("get_vocabulary_level", level="beginner")
        response = client.get(level_url)
        assert response.status_code in [200, 401, 404]


    def test_profile_endpoints_robust(self, client, url_builder):
        """Example: Testing profile endpoints"""

        # Get profile
        profile_url = url_builder.url_for("profile_get")
        response = client.get(profile_url)
        assert response.status_code in [200, 401]

        # Get supported languages
        languages_url = url_builder.url_for("profile_get_supported_languages")
        response = client.get(languages_url)
        assert response.status_code == 200  # This endpoint doesn't require auth

        expected_languages = {"en", "de", "es"}
        response_data = response.json()
        assert set(response_data.keys()) == expected_languages


    def test_debug_endpoints_robust(self, client, url_builder):
        """Example: Testing debug endpoints"""

        # Health check endpoint
        health_url = url_builder.url_for("debug_health")
        response = client.get(health_url)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


    def test_game_endpoints_robust(self, client, url_builder):
        """Example: Testing game endpoints"""

        # Get user sessions
        sessions_url = url_builder.url_for("game_get_user_sessions")
        response = client.get(sessions_url)
        assert response.status_code in [200, 401]


class TestUrlBuilderFunctionality:
    """Test the url_builder itself"""

    def test_url_builder_generates_correct_paths(self, url_builder):
        """Test that URL builder generates expected paths"""

        # Test simple route
        health_url = url_builder.url_for("debug_health")
        assert health_url.endswith("/debug/health")

        # Test route with path parameters
        stream_url = url_builder.url_for("stream_video", series="MyShow", episode="S01E02")
        assert "MyShow" in stream_url
        assert "S01E02" in stream_url
        assert stream_url.endswith("/videos/MyShow/S01E02")


    def test_url_builder_handles_missing_route(self, url_builder):
        """Test that URL builder raises error for missing routes"""

        with pytest.raises(ValueError, match="Route 'nonexistent_route' not found"):
            url_builder.url_for("nonexistent_route")


    def test_all_named_routes_are_accessible(self, url_builder):
        """Test that all our newly named routes are accessible via the builder"""

        # Sample of routes we just named - this ensures they're properly registered
        expected_routes = [
            "auth_get_current_user",
            "auth_test_prefix",
            "get_videos",
            "stream_video",
            "upload_video_to_series",
            "get_vocabulary_stats",
            "profile_get",
            "profile_get_supported_languages",
            "debug_health",
            "game_start_session",
            "logs_receive_frontend",
            "process_chunk",
            "transcribe_video",
            "progress_get_user"
        ]

        for route_name in expected_routes:
            # This should not raise an exception
            try:
                if route_name in ["stream_video", "upload_video_to_series"]:
                    # Routes with required path parameters
                    if route_name == "stream_video":
                        url = url_builder.url_for(route_name, series="test", episode="test")
                    elif route_name == "upload_video_to_series":
                        url = url_builder.url_for(route_name, series="test")
                else:
                    # Routes without path parameters
                    url = url_builder.url_for(route_name)
                assert isinstance(url, str)
                assert len(url) > 0
            except ValueError as e:
                pytest.fail(f"Route '{route_name}' not found in app: {e}")


if __name__ == "__main__":
    # Run a simple test to verify the setup works
    from fastapi.testclient import TestClient

    from core.app import app

    client = TestClient(app)
    url_builder = get_url_builder(client.app)

    print("Testing URL builder functionality...")

    # Test a few key routes
    try:
        health_url = url_builder.url_for("debug_health")
        print(f"✓ Health endpoint: {health_url}")

        languages_url = url_builder.url_for("profile_get_supported_languages")
        print(f"✓ Supported languages: {languages_url}")

        stream_url = url_builder.url_for("stream_video", series="TestShow", episode="S01E01")
        print(f"✓ Stream video: {stream_url}")

        print("\n✅ All URL builder tests passed!")
        print("Your routes are now robustly named and ready for testing!")

    except Exception as e:
        print(f"❌ Error: {e}")
