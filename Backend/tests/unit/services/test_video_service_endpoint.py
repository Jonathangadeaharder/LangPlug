"""
Unit tests for video service endpoint functionality
Tests the processChunk API endpoint with proper mocking and assertions
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.auth_helpers import AuthTestHelperAsync


class TestVideoServiceEndpoint:
    """Test video service API endpoint functionality"""

    @pytest.mark.asyncio
    async def test_process_chunk_endpoint_success(self, async_client: AsyncClient):
        """Test processChunk endpoint returns task ID on successful request"""

        # Arrange: Authenticate user
        auth_flow = await AuthTestHelperAsync.register_and_login_async(async_client)
        headers = auth_flow["headers"]

        # Arrange: Prepare valid test request
        test_request = {"video_path": "test_video.mp4", "start_time": 0, "end_time": 300}

        # Mock the file system and processing dependencies
        with (
            patch("api.routes.episode_processing_routes.Path") as mock_path_class,
            patch("api.routes.episode_processing_routes.run_chunk_processing") as mock_run_processing,
        ):
            # Setup mocks - create a mock path that exists
            mock_path_instance = AsyncMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
            mock_path_class.return_value = mock_path_instance

            # Act: Call the endpoint
            response = await async_client.post("/api/process/chunk", json=test_request, headers=headers)

            # Assert: Verify successful response
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

            # Assert: Verify response structure
            result = response.json()
            assert "task_id" in result
            assert "status" in result
            assert result["status"] == "started"

            # Verify the background task was scheduled
            mock_run_processing.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_chunk_endpoint_unauthorized(self, async_client: AsyncClient):
        """Test processChunk endpoint rejects unauthorized requests"""

        # Arrange: Prepare test request without authentication
        test_request = {"video_path": "test_video.mp4", "start_time": 0, "end_time": 300}

        # Act: Call endpoint without auth headers
        response = await async_client.post("/api/process/chunk", json=test_request)

        # Assert: Verify unauthorized response
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    @pytest.mark.asyncio
    async def test_process_chunk_endpoint_invalid_data(self, async_client: AsyncClient):
        """Test processChunk endpoint validates required fields"""

        # Arrange: Authenticate user
        auth_flow = await AuthTestHelperAsync.register_and_login_async(async_client)
        headers = auth_flow["headers"]

        # Arrange: Prepare invalid test request (missing required fields)
        invalid_request = {
            "video_path": "test_video.mp4"
            # Missing start_time and end_time
        }

        # Act: Call endpoint with invalid data
        response = await async_client.post("/api/process/chunk", json=invalid_request, headers=headers)

        # Assert: Verify validation error response
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

        # Assert: Verify error details
        error_data = response.json()
        assert "error" in error_data
        assert "details" in error_data["error"]

    @pytest.mark.asyncio
    async def test_process_chunk_endpoint_service_error(self, async_client: AsyncClient):
        """Test processChunk endpoint handles service errors gracefully"""

        # Arrange: Authenticate user
        auth_flow = await AuthTestHelperAsync.register_and_login_async(async_client)
        headers = auth_flow["headers"]

        # Arrange: Prepare valid test request
        test_request = {"video_path": "test_video.mp4", "start_time": 0, "end_time": 300}

        # Mock settings.get_videos_path() to return a mock path
        with patch("api.routes.episode_processing_routes.settings") as mock_settings:
            # Create a mock path that will be returned by get_videos_path()
            mock_videos_base_path = MagicMock()
            mock_settings.get_videos_path.return_value = mock_videos_base_path

            # Mock the path division operation (base_path / filename)
            mock_full_path = MagicMock()
            mock_full_path.exists.return_value = False  # File doesn't exist
            mock_videos_base_path.__truediv__.return_value = mock_full_path

            # Act: Call the endpoint
            response = await async_client.post("/api/process/chunk", json=test_request, headers=headers)

            # Assert: Verify file not found error
            assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"

            # Assert: Verify error response structure
            error_data = response.json()
            assert "detail" in error_data
            assert "not found" in error_data["detail"].lower()
