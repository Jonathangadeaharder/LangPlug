"""In-process integration tests using TestClient (replacing external process tests)."""

from __future__ import annotations

import pytest

from tests.helpers import (
    AsyncAuthHelper,
    assert_auth_response_structure,
    assert_authentication_error,
    assert_json_response,
    assert_status_code,
    assert_user_response_structure,
    assert_vocabulary_response_structure,
)


@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Integration tests for authentication endpoints using in-process client."""

    @pytest.mark.anyio
    async def test_When_user_registration_flow_completed_Then_user_created_successfully(self, async_client):
        """Complete user registration flow should create user successfully."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)

        # Act
        user, registration_data = await auth_helper.register_user()

        # Assert
        assert_user_response_structure(registration_data)
        assert registration_data["username"] == user.username
        assert registration_data["is_active"] is True
        assert registration_data["is_superuser"] is False

    @pytest.mark.anyio
    async def test_When_user_registered_and_logs_in_Then_receives_valid_token(self, async_client):
        """User should be able to login after registration and receive valid token."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        user, _ = await auth_helper.register_user()

        # Act
        token, login_data = await auth_helper.login_user(user)

        # Assert
        assert_auth_response_structure(login_data)
        assert len(token) > 20, "JWT token should be non-trivial length"
        assert login_data["token_type"] == "bearer"

    @pytest.mark.anyio
    async def test_When_authenticated_user_accesses_profile_Then_profile_returned(self, async_client):
        """Authenticated user should be able to access their profile."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.get("/api/auth/me", headers=headers)

        # Assert
        profile = assert_json_response(response, 200)
        assert_user_response_structure(profile)
        assert profile["username"] == user.username

    @pytest.mark.anyio
    async def test_When_unauthenticated_user_accesses_protected_endpoint_Then_authentication_required(
        self, async_client
    ):
        """Unauthenticated access to protected endpoint should require authentication."""
        # Act
        response = await async_client.get("/api/auth/me")

        # Assert
        assert_authentication_error(response)

    @pytest.mark.anyio
    async def test_When_user_logs_out_Then_token_invalidated(self, async_client):
        """User logout should invalidate the token."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, token, headers = await auth_helper.create_authenticated_user()

        # Verify token works initially
        response = await async_client.get("/api/auth/me", headers=headers)
        assert_status_code(response, 200)

        # Act
        logout_data = await auth_helper.logout_user(token)

        # Assert
        assert "success" in logout_data or "message" in logout_data

        # Token should now be invalid
        response = await async_client.get("/api/auth/me", headers=headers)
        assert response.status_code in [401, 403], "Token should be invalid after logout"


@pytest.mark.integration
class TestVocabularyEndpoints:
    """Integration tests for vocabulary management endpoints."""

    @pytest.mark.anyio
    async def test_When_authenticated_user_gets_vocabulary_stats_Then_stats_returned(self, async_client):
        """Authenticated user should be able to get vocabulary statistics."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.get("/api/vocabulary/stats", headers=headers)

        # Assert
        data = assert_json_response(response, 200)

        # Basic structure validation
        required_fields = ["levels", "total_words", "total_known"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    @pytest.mark.anyio
    async def test_When_authenticated_user_gets_supported_languages_Then_languages_returned(self, async_client):
        """Authenticated user should be able to get supported languages."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.get("/api/vocabulary/languages", headers=headers)

        # Assert
        data = assert_json_response(response, 200)
        assert "languages" in data
        assert isinstance(data["languages"], list)

    @pytest.mark.anyio
    async def test_When_authenticated_user_gets_vocabulary_level_Then_words_returned(self, async_client):
        """Authenticated user should be able to get vocabulary for a specific level."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "de", "limit": 10},
            headers=headers,
        )

        # Assert
        data = assert_json_response(response, 200)
        assert_vocabulary_response_structure(data)

    @pytest.mark.anyio
    async def test_When_authenticated_user_marks_word_known_Then_success_returned(self, async_client):
        """Authenticated user should be able to mark a word as known."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        from uuid import uuid4

        concept_id = str(uuid4())

        # Act
        response = await async_client.post(
            "/api/vocabulary/mark-known",
            json={"concept_id": concept_id, "known": True},
            headers=headers,
        )

        # Assert
        data = assert_json_response(response, 200)
        assert "success" in data
        assert "concept_id" in data
        assert "known" in data

    @pytest.mark.anyio
    async def test_When_unauthenticated_user_accesses_vocabulary_Then_authentication_required(self, async_client):
        """Unauthenticated access to vocabulary endpoints should require authentication."""
        # Act
        endpoints = [
            "/api/vocabulary/stats",
            "/api/vocabulary/languages",
            "/api/vocabulary/library/A1",
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint)

            # Assert
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require authentication"

    @pytest.mark.anyio
    async def test_When_bulk_mark_operation_performed_Then_batch_update_succeeds(self, async_client):
        """Authenticated user should be able to perform bulk mark operations."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1", "target_language": "de", "known": True},
            headers=headers,
        )

        # Assert
        data = assert_json_response(response, 200)
        assert "success" in data
        assert "level" in data
        assert "word_count" in data


@pytest.mark.integration
class TestEndpointValidation:
    """Integration tests for endpoint validation and error handling."""

    @pytest.mark.anyio
    async def test_When_invalid_vocabulary_level_requested_Then_validation_error_returned(self, async_client):
        """Request for invalid vocabulary level should return validation error."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.get("/api/vocabulary/library/INVALID_LEVEL", headers=headers)

        # Assert
        assert response.status_code == 422, "Invalid level should return validation error"

    @pytest.mark.anyio
    async def test_When_mark_known_without_concept_id_Then_validation_error_returned(self, async_client):
        """Mark known request without concept_id should return validation error."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.post(
            "/api/vocabulary/mark-known",
            json={"known": True},  # Missing concept_id
            headers=headers,
        )

        # Assert
        assert response.status_code == 422, "Missing concept_id should return validation error"

    @pytest.mark.anyio
    async def test_When_mark_known_with_invalid_uuid_Then_validation_error_returned(self, async_client):
        """Mark known request with invalid UUID should return validation error."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.post(
            "/api/vocabulary/mark-known",
            json={"concept_id": "not-a-uuid", "known": True},
            headers=headers,
        )

        # Assert
        assert response.status_code == 422, "Invalid UUID should return validation error"

    @pytest.mark.anyio
    async def test_When_bulk_mark_with_invalid_level_Then_validation_error_returned(self, async_client):
        """Bulk mark with invalid level should return validation error."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)
        _user, _token, headers = await auth_helper.create_authenticated_user()

        # Act
        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "INVALID", "target_language": "de", "known": True},
            headers=headers,
        )

        # Assert
        assert response.status_code == 422, "Invalid level should return validation error"


@pytest.mark.integration
class TestEndpointSecurity:
    """Integration tests for endpoint security and authorization."""

    @pytest.mark.anyio
    async def test_When_malformed_token_used_Then_authentication_fails(self, async_client):
        """Malformed authorization token should fail authentication."""
        # Arrange
        malformed_headers = {"Authorization": "Malformed token123"}

        # Act
        response = await async_client.get("/api/auth/me", headers=malformed_headers)

        # Assert
        assert_authentication_error(response)

    @pytest.mark.anyio
    async def test_When_expired_token_used_Then_authentication_fails(self, async_client):
        """Expired token should fail authentication."""
        # Arrange
        expired_headers = {"Authorization": "Bearer expired_token_that_should_fail"}

        # Act
        response = await async_client.get("/api/auth/me", headers=expired_headers)

        # Assert
        assert_authentication_error(response)

    @pytest.mark.anyio
    async def test_When_multiple_users_access_own_data_Then_data_isolated(self, async_client):
        """Multiple users should only access their own data."""
        # Arrange
        auth_helper = AsyncAuthHelper(async_client)

        user1, _token1, headers1 = await auth_helper.create_authenticated_user()
        user2, _token2, headers2 = await auth_helper.create_authenticated_user()

        # Act
        response1 = await async_client.get("/api/auth/me", headers=headers1)
        response2 = await async_client.get("/api/auth/me", headers=headers2)

        # Assert
        data1 = assert_json_response(response1, 200)
        data2 = assert_json_response(response2, 200)

        assert data1["username"] == user1.username
        assert data2["username"] == user2.username
        assert data1["username"] != data2["username"], "Users should have different data"


@pytest.mark.integration
@pytest.mark.slow
class TestEndpointPerformance:
    """Integration tests for endpoint performance characteristics."""

    @pytest.mark.anyio
    async def test_When_health_endpoint_called_Then_responds_quickly(self, async_client):
        """Health endpoint should respond quickly."""
        import time

        # Act
        start_time = time.time()
        response = await async_client.get("/health")
        elapsed = time.time() - start_time

        # Assert
        data = assert_json_response(response, 200)
        assert data["status"] == "healthy"
        assert elapsed < 1.0, f"Health endpoint took {elapsed:.3f}s, should be < 1.0s"

    @pytest.mark.anyio
    async def test_When_concurrent_auth_requests_made_Then_all_succeed(self, async_client):
        """Concurrent authentication requests should all succeed."""
        import asyncio

        # Arrange
        auth_helper = AsyncAuthHelper(async_client)

        # Create multiple users concurrently
        async def create_user():
            _user, _token, headers = await auth_helper.create_authenticated_user()
            response = await async_client.get("/api/auth/me", headers=headers)
            return assert_json_response(response, 200)

        # Act
        results = await asyncio.gather(*[create_user() for _ in range(3)])

        # Assert
        assert len(results) == 3
        usernames = [result["username"] for result in results]
        assert len(set(usernames)) == 3, "All users should have unique usernames"
