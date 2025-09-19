"""In-process tests for minimal debug endpoints using httpx async client fixture."""


import pytest


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenMinimalPostCalled_ThenSucceeds(async_client):
    r = await async_client.post("/api/debug/test-minimal", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenWithDataPostCalled_ThenSucceeds(async_client):
    payload = {"test": "value", "number": 123}
    r = await async_client.post("/api/debug/test-with-data", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["received_data"] == payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenwith_data_postWithnon_object_ThenRejects(async_client):
    """Invalid input: passing a scalar results in 422 validation error."""
    response = await async_client.post("/api/debug/test-with-data", json="just a string")

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenDebughealthCalled_ThenSucceeds(async_client):
    r = await async_client.get("/api/debug/health")
    assert r.status_code == 200
