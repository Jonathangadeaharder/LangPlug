"""In-process tests for debug endpoints using httpx async client fixture."""

from datetime import datetime

import pytest
from tests.assertion_helpers import assert_validation_error_response


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenDebugFrontendLogsCalled_ThenSucceeds(async_client):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "category": "Test",
        "message": "Test log from direct API call",
        "data": {"test": True},
        "url": "http://localhost:3000/test",
        "userAgent": "TestScript/1.0",
    }
    r = await async_client.post("/api/debug/frontend-logs", json=log_entry)
    assert r.status_code == 200
    assert r.json().get("success") is True


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenDebugFrontendLogs_MissingLevelCalled_ThenSucceeds(async_client):
    """Invalid input: omitting required fields returns validation error."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "category": "Test",
        "message": "Missing level should fail",
    }

    response = await async_client.post("/api/debug/frontend-logs", json=log_entry)

    assert_validation_error_response(response, "level")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenDebughealthCalled_ThenSucceeds(async_client):
    r = await async_client.get("/api/debug/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
