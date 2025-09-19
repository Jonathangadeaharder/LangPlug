"""
Happy-path test for /process/full-pipeline using a fast fake background task.
"""
from __future__ import annotations

import asyncio

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFullPipelineFastCalled_ThenSucceeds(async_client, monkeypatch):
    """Happy path: full pipeline kicks off and reports completion quickly."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)
    from api.routes import processing as proc

    async def fake_pipeline(video_path_str: str, task_id: str, task_progress, user_id: int):
        task_progress[task_id] = proc.ProcessingStatus(
            status="completed",
            progress=100.0,
            current_step="done",
            message="ok",
        )

    monkeypatch.setattr(proc, "run_processing_pipeline", fake_pipeline)

    request_body = {
        "video_path": "any.mp4",
        "source_lang": "de",
        "target_lang": "en",
    }

    response = await async_client.post(
        "/api/process/full-pipeline", json=request_body, headers=auth["headers"]
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    await asyncio.sleep(0.1)

    progress_response = await async_client.get(
        f"/api/process/progress/{task_id}", headers=auth["headers"]
    )
    assert progress_response.status_code == 200
    progress = progress_response.json()
    assert progress["status"] == "completed"
    assert progress["progress"] == 100.0


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenfull_pipelineWithoutVideoPath_ThenReturnsError(async_client):
    """Invalid input: missing video path yields validation errors."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        "/api/process/full-pipeline",
        json={"source_lang": "en", "target_lang": "de"},
        headers=auth["headers"],
    )

    assert response.status_code == 422
