"""High-level workflow smoke tests."""

from __future__ import annotations

import pytest

from tests.helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenfull_user_workflowCalled_ThenSucceeds(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    status_code, profile = await AuthTestHelperAsync.get_current_user_async(async_client, flow["token"])
    assert status_code == 200
    assert profile["username"] == flow["user_data"]["username"]

    status_code, _ = await AuthTestHelperAsync.logout_user_async(async_client, flow["token"])
    assert status_code == 204
