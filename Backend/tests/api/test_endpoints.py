"""High-level API endpoint smoke tests complying with the CDD/TDD rules."""
from __future__ import annotations

import datetime as dt

import pytest
from tests.assertion_helpers import assert_json_error_response


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenHealthEndpointCalled_ThenReportsstatus(async_client):
    """Happy path: /health reports overall status and metadata."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "version" in payload
    dt.datetime.fromisoformat(payload["timestamp"])  # raises if not ISO formatted


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenunknown_routeCalled_ThenReturnscontract_404(async_client):
    """Invalid input: unknown route returns consistent 404 response."""
    response = await async_client.get("/api/does-not-exist")

    assert_json_error_response(response, 404)
    payload = response.json()
    # Handle both FastAPI standard format and custom error format
    if "error" in payload and "message" in payload["error"]:
        assert payload["error"]["message"] == "Not Found"
    else:
        assert payload.get("detail") == "Not Found"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenHealthEndpoint_Thenread_only(async_client):
    """Boundary: POSTing to /health is not allowed and surfaces 405."""
    response = await async_client.post("/health")

    assert_json_error_response(response, 405)
    payload = response.json()
    # Handle both FastAPI standard format and custom error format
    if "error" in payload and "message" in payload["error"]:
        assert payload["error"]["message"] == "Method Not Allowed"
    else:
        assert payload.get("detail") == "Method Not Allowed"
