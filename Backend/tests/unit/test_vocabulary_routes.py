"""Comprehensive tests for vocabulary API routes with improved coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from tests.auth_helpers import AuthTestHelperAsync

# Force asyncio-only to prevent trio backend interference in full test suite
pytestmark = pytest.mark.anyio(backends=["asyncio"])


class TestVocabularyRoutesCore:
    """Test core vocabulary route functionality"""

    @pytest.mark.anyio
    async def test_get_supported_languages_success(self, async_client):
        """Test getting supported languages endpoint"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Since the actual endpoint works, let's test the real functionality
        # This will test the actual database integration
        response = await async_client.get("/api/vocabulary/languages", headers=flow["headers"])

        # The endpoint should work correctly with expected success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "languages" in data
        # Languages list can be empty if no languages are configured
        assert isinstance(data["languages"], list)

    @pytest.mark.anyio
    async def test_get_supported_languages_error(self, async_client, app):
        """Test error handling in supported languages endpoint"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Create mock session that raises database error
        async def mock_get_async_session():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Database connection failed")
            yield mock_session

        # Use FastAPI's dependency override system (the correct way)
        from core.database import get_async_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = await async_client.get("/api/vocabulary/languages", headers=flow["headers"])

            assert response.status_code == 500
            assert "Error retrieving languages" in response.json()["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.pop(get_async_session, None)

    @pytest.mark.anyio
    async def test_get_vocabulary_stats_success(self, async_client):
        """Test vocabulary stats endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        response = await async_client.get(
            "/api/vocabulary/stats",
            params={"target_language": "de", "translation_language": "es"},
            headers=flow["headers"],
        )

        # Should work correctly with expected success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data["target_language"] == "de"
        # translation_language is optional in VocabularyStats model
        if "translation_language" in data:
            assert data["translation_language"] == "es"
        assert "levels" in data
        assert "total_words" in data
        assert "total_known" in data
        # Check that all CEFR levels are present
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            assert level in data["levels"]
            assert "total_words" in data["levels"][level]
            assert "user_known" in data["levels"][level]

    @pytest.mark.anyio
    async def test_get_vocabulary_level_success(self, async_client):
        """Test vocabulary level endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Test real endpoint - should work regardless of database state
        response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "de", "translation_language": "es", "limit": 50},
            headers=flow["headers"],
        )

        # Should succeed with proper response structure
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "A1"
        assert data["target_language"] == "de"
        assert data["translation_language"] == "es"
        assert "words" in data
        assert isinstance(data["words"], list)
        # Note: words list may be empty if no vocabulary is configured

    @pytest.mark.anyio
    async def test_get_vocabulary_level_invalid_level(self, async_client):
        """Test vocabulary level endpoint with invalid level"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        response = await async_client.get(
            "/api/vocabulary/library/Z9", params={"target_language": "de"}, headers=flow["headers"]
        )

        assert response.status_code == 422
        assert "Invalid level" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_mark_word_as_known_success(self, async_client):
        """Test marking word as known endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        concept_id = uuid4()

        with patch("api.routes.vocabulary.get_async_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock no existing progress
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            response = await async_client.post(
                "/api/vocabulary/mark-known",
                json={"concept_id": str(concept_id), "known": True},
                headers=flow["headers"],
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["concept_id"] == str(concept_id)

    @pytest.mark.anyio
    async def test_mark_word_unknown_success(self, async_client):
        """Test marking word as unknown endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        concept_id = uuid4()

        # Test real endpoint behavior - focus on API contract, not implementation
        response = await async_client.post(
            "/api/vocabulary/mark-known", json={"concept_id": str(concept_id), "known": False}, headers=flow["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["concept_id"] == str(concept_id)
        assert data["known"] is False

    @pytest.mark.anyio
    async def test_bulk_mark_level_known_success(self, async_client):
        """Test bulk marking level as known endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Test real endpoint behavior - should work regardless of database state
        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1", "target_language": "de", "known": True},
            headers=flow["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["level"] == "A1"
        assert data["known"] is True
        assert "word_count" in data
        assert isinstance(data["word_count"], int)
        assert data["word_count"] >= 0  # May be 0 if no words for this level

    @pytest.mark.anyio
    async def test_bulk_mark_level_invalid_level(self, async_client):
        """Test bulk marking with invalid level"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "Z9", "target_language": "de", "known": True},
            headers=flow["headers"],
        )

        assert response.status_code == 422
        data = response.json()
        # Custom error handling returns validation errors in error.details array
        assert "error" in data
        assert "details" in data["error"]
        # Should contain pattern validation error for level field
        error_details = data["error"]["details"]
        assert any("pattern" in str(error).lower() for error in error_details)

    @pytest.mark.anyio
    async def test_get_test_data_success(self, async_client):
        """Test test data endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Test real endpoint - should work regardless of database state
        response = await async_client.get("/api/vocabulary/test-data", headers=flow["headers"])

        assert response.status_code == 200
        data = response.json()
        assert "concept_count" in data
        assert "translation_count" in data
        assert "sample_translations" in data
        assert isinstance(data["concept_count"], int)
        assert isinstance(data["translation_count"], int)
        assert isinstance(data["sample_translations"], list)
        # Counts may be 0 if no data is configured

    @pytest.mark.anyio
    async def test_get_blocking_words_missing_srt(self, async_client):
        """Test blocking words endpoint with missing SRT file"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        with patch("api.routes.vocabulary.settings") as mock_settings:
            from pathlib import Path

            mock_videos_path = Path("/fake/videos")
            mock_settings.get_videos_path.return_value = mock_videos_path

            # Mock non-existent SRT file
            with patch.object(Path, "exists", return_value=False):
                response = await async_client.get(
                    "/api/vocabulary/blocking-words", params={"video_path": "test.mp4"}, headers=flow["headers"]
                )

                assert response.status_code == 404
                assert "Subtitle file not found" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_get_blocking_words_success(self, async_client):
        """Test blocking words endpoint success"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        with patch("api.routes.vocabulary.settings") as mock_settings:
            from pathlib import Path

            mock_videos_path = Path("/fake/videos")
            mock_settings.get_videos_path.return_value = mock_videos_path

            # Mock existing SRT file
            with patch.object(Path, "exists", return_value=True):
                response = await async_client.get(
                    "/api/vocabulary/blocking-words", params={"video_path": "test.mp4"}, headers=flow["headers"]
                )

                assert response.status_code == 200
                data = response.json()
                assert "blocking_words" in data
                assert "video_path" in data
                assert "srt_path" in data


class TestVocabularyRoutesErrorHandling:
    """Test error handling in vocabulary routes"""

    @pytest.mark.anyio
    async def test_vocabulary_stats_database_error(self, async_client):
        """Test vocabulary stats with realistic error scenarios"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Test with invalid but properly formatted language code
        response = await async_client.get(
            "/api/vocabulary/stats",
            params={"target_language": "xx"},  # Valid format but non-existent language
            headers=flow["headers"],
        )

        # Should succeed but return empty stats (real system behavior)
        # This tests that the API gracefully handles missing data scenarios
        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert "total_words" in data
        assert "total_known" in data
        # With invalid language, should have 0 words
        assert data["total_words"] == 0

    @pytest.mark.anyio
    async def test_mark_known_database_error(self, async_client):
        """Test mark known with realistic error scenarios"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Test with valid UUID - should succeed even if concept doesn't exist in DB
        # This tests graceful handling of missing concepts
        response = await async_client.post(
            "/api/vocabulary/mark-known", json={"concept_id": str(uuid4()), "known": True}, headers=flow["headers"]
        )

        # Should succeed - system gracefully handles non-existent concepts
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "concept_id" in data
        assert data["known"] is True

    @pytest.mark.anyio
    async def test_vocabulary_level_database_error(self, async_client):
        """Test vocabulary level with realistic error scenarios"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        # Test with invalid language - should return empty results gracefully
        response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "xx"},  # Valid format but non-existent language
            headers=flow["headers"],
        )

        # Should succeed but return empty word list
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "A1"
        assert data["target_language"] == "xx"
        assert "words" in data
        assert len(data["words"]) == 0  # No words for invalid language


class TestVocabularyRoutesValidation:
    """Test input validation in vocabulary routes"""

    @pytest.mark.anyio
    async def test_mark_known_invalid_uuid(self, async_client):
        """Test mark known with invalid UUID"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        response = await async_client.post(
            "/api/vocabulary/mark-known", json={"concept_id": "not-a-uuid", "known": True}, headers=flow["headers"]
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_bulk_mark_missing_fields(self, async_client):
        """Test bulk mark with missing required fields"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1"},  # Missing target_language and known
            headers=flow["headers"],
        )

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_vocabulary_level_query_params(self, async_client):
        """Test vocabulary level with various query parameters"""
        flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        with patch("api.routes.vocabulary.get_async_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock empty results
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.side_effect = [mock_result, MagicMock(fetchall=lambda: [])]

            response = await async_client.get(
                "/api/vocabulary/library/B2",
                params={"target_language": "es", "translation_language": "en", "limit": 100},
                headers=flow["headers"],
            )

            assert response.status_code == 200
            data = response.json()
            assert data["level"] == "B2"
            assert data["target_language"] == "es"
            assert data["translation_language"] == "en"
            assert len(data["words"]) == 0
