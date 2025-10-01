"""High-level API endpoint smoke tests complying with the CDD/TDD rules."""

from __future__ import annotations

import datetime as dt

import pytest

from tests.assertion_helpers import assert_json_error_response


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenHealthEndpointCalled_ThenReportsstatus(async_http_client):
    """Happy path: /health reports overall status and metadata."""
    response = await async_http_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "version" in payload
    dt.datetime.fromisoformat(payload["timestamp"])  # raises if not ISO formatted


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenunknown_routeCalled_ThenReturnscontract_404(async_http_client):
    """Invalid input: unknown route returns consistent 404 response."""
    response = await async_http_client.get("/api/does-not-exist")

    assert_json_error_response(response, 404)
    payload = response.json()
    # Handle both FastAPI standard format and custom error format
    if "error" in payload and "message" in payload["error"]:
        assert payload["error"]["message"] in ["Not Found", "Endpoint not found in API contract"]
    else:
        # Accept both the standard FastAPI message and the contract middleware message
        assert payload.get("detail") in ["Not Found", "Endpoint not found in API contract"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenHealthEndpoint_Thenread_only(async_http_client):
    """Boundary: POSTing to /health is not allowed and surfaces 405 or 404."""
    response = await async_http_client.post("/health")

    # Contract middleware might return 404 (undefined endpoint) or FastAPI might return 405 (method not allowed)
    assert response.status_code in [404, 405], f"Expected 404 or 405, got {response.status_code}"
    payload = response.json()

    if response.status_code == 404:
        # Contract middleware response format
        assert payload.get("detail") in ["Not Found", "Endpoint not found in API contract"]
    # FastAPI 405 response format
    elif "error" in payload and "message" in payload["error"]:
        assert payload["error"]["message"] == "Method Not Allowed"
    else:
        assert payload.get("detail") == "Method Not Allowed"
