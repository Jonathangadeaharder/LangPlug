"""Protective tests for the authentication round trip latency and response shape."""

from __future__ import annotations

import os
import time

import pytest

from tests.auth_helpers import AuthTestHelper

AUTH_ROUND_TRIP_BUDGET = 1.5


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy performance test in constrained sandbox",
)
@pytest.mark.timeout(30)
async def test_Whenregistration_and_login_round_tripCalled_ThenSucceeds(async_client) -> None:
    """A full register→login cycle should finish quickly and return the bearer token contract."""
    user_data = AuthTestHelper.generate_unique_user_data()

    started = time.perf_counter()
    reg_status, _ = await AuthTestHelper.register_user_async(async_client, user_data)
    login_status, login_payload = await AuthTestHelper.login_user_async(
        async_client,
        user_data["email"],
        user_data["password"],
    )
    elapsed = time.perf_counter() - started

    assert reg_status == 201
    assert login_status == 200
    assert login_payload["token_type"].lower() == "bearer"
    assert "access_token" in login_payload
    assert elapsed < AUTH_ROUND_TRIP_BUDGET


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("SKIP_DB_HEAVY_TESTS") == "1",
    reason="Skipping DB-heavy performance test in constrained sandbox",
)
@pytest.mark.timeout(30)
async def test_login_with_WrongPassword_fails_fast(async_client) -> None:
    """Invalid credentials should be rejected promptly without leaking token data."""
    user_data = AuthTestHelper.generate_unique_user_data()
    await AuthTestHelper.register_user_async(async_client, user_data)

    started = time.perf_counter()
    status, payload = await AuthTestHelper.login_user_async(
        async_client,
        user_data["email"],
        "TotallyWrong123!",
    )
    elapsed = time.perf_counter() - started

    # Invalid credentials should return 401 (unauthorized)
    assert status == 401, f"Expected 401 (unauthorized - invalid credentials), got {status}"
    assert "access_token" not in payload
    assert elapsed < AUTH_ROUND_TRIP_BUDGET
