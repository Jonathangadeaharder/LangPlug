"""User profile route tests following the CDD/TDD policies."""
from __future__ import annotations

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenget_profileCalled_ThenReturnsauthenticated_user(async_http_client, url_builder):
    """Happy path: /profile returns the authenticated user's public profile."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)
    profile_url = url_builder.url_for("profile_get")

    response = await async_http_client.get(profile_url, headers=flow["headers"])

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == flow["user_data"]["username"]
    assert "id" in data


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenget_profileWithoutauthentication_ThenReturnsError(async_http_client, url_builder):
    """Invalid input: missing authorization header yields 401."""
    profile_url = url_builder.url_for("profile_get")

    response = await async_http_client.get(profile_url)

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_WhenUpdateLanguagesAcceptsValidPayload_ThenSucceeds(async_http_client, url_builder):
    """Happy path: language update persists preferred codes."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)
    languages_url = url_builder.url_for("profile_update_languages")

    response = await async_http_client.put(
        languages_url,
        json={"native_language": "en", "target_language": "de"},
        headers=flow["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["native_language"]["code"] == "en"
    assert body["target_language"]["code"] == "de"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_Whenupdate_languagesWithduplicate_codes_ThenRejects(async_http_client, url_builder):
    """Boundary: native and target languages must differ."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)
    languages_url = url_builder.url_for("profile_update_languages")

    response = await async_http_client.put(
        languages_url,
        json={"native_language": "en", "target_language": "en"},
        headers=flow["headers"],
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_WhenSupportedLanguagesListsKnownCodes_ThenSucceeds(async_http_client, url_builder):
    """Happy path: supported languages endpoint enumerates known codes."""
    languages_url = url_builder.url_for("profile_get_supported_languages")

    response = await async_http_client.get(languages_url)

    assert response.status_code == 200
    codes = response.json()
    assert "en" in codes and "de" in codes
