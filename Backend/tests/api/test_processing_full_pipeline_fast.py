"""Processing pipeline API tests."""

from __future__ import annotations

import pytest

from api.models.processing import ProcessingStatus
from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenfull_pipeline_started_ThenReturnsTaskId(async_client, monkeypatch):
    """Full pipeline should start and return a task ID."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    # Mock the processing pipeline

    async def mock_pipeline(video_path_str: str, task_id: str, task_progress, user_id: int):
        task_progress[task_id] = ProcessingStatus(
            status="completed",
            progress=100.0,
            current_step="done",
            message="Processing complete",
        )

    monkeypatch.setattr("api.routes.episode_processing_routes.run_processing_pipeline", mock_pipeline)

    request_body = {
        "video_path": "test_video.mp4",
        "source_lang": "de",
        "target_lang": "en",
    }

    response = await async_client.post("/api/process/full-pipeline", json=request_body, headers=auth["headers"])

    assert response.status_code == 200
    assert "task_id" in response.json()


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenpipeline_progress_requested_ThenReturnsStatus(async_client, monkeypatch):
    """Pipeline progress endpoint should return current status."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    # Mock the processing pipeline

    async def mock_pipeline(video_path_str: str, task_id: str, task_progress, user_id: int):
        task_progress[task_id] = ProcessingStatus(
            status="completed",
            progress=100.0,
            current_step="done",
            message="Processing complete",
        )

    monkeypatch.setattr("api.routes.episode_processing_routes.run_processing_pipeline", mock_pipeline)

    # Start processing
    request_body = {
        "video_path": "test_video.mp4",
        "source_lang": "de",
        "target_lang": "en",
    }

    response = await async_client.post("/api/process/full-pipeline", json=request_body, headers=auth["headers"])
    task_id = response.json()["task_id"]

    # Mock completes synchronously - check progress immediately
    progress_response = await async_client.get(f"/api/process/progress/{task_id}", headers=auth["headers"])

    assert progress_response.status_code == 200
    progress_data = progress_response.json()
    assert "status" in progress_data
    assert "progress" in progress_data


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenpipeline_missing_video_path_ThenReturnsValidationError(async_client):
    """Pipeline without video path should return validation error."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/process/full-pipeline",
        json={"source_lang": "en", "target_lang": "de"},
        headers=auth["headers"],
    )

    assert response.status_code == 422
