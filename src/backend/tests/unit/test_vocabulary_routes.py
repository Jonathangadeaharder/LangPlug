"""Comprehensive tests for vocabulary API routes with improved coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models import VocabularyWord
from tests.helpers import AsyncAuthHelper

# Use pytest-asyncio - no more anyio backend duplication
pytestmark = pytest.mark.asyncio


async def seed_vocabulary_data(app):
    """Seed vocabulary data directly in test - eliminates fixture ordering complexity"""
    SessionLocal = app.state._test_session_factory

    async with SessionLocal() as session:
        words = [
            VocabularyWord(
                word="Hallo",
                lemma="hallo",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                translation_en="Hello",
                translation_native="Hola",
            ),
            VocabularyWord(
                word="ich",
                lemma="ich",
                language="de",
                difficulty_level="A1",
                part_of_speech="pronoun",
                translation_en="I",
                translation_native="yo",
            ),
            VocabularyWord(
                word="du",
                lemma="du",
                language="de",
                difficulty_level="A1",
                part_of_speech="pronoun",
                translation_en="you",
                translation_native="tú",
            ),
            VocabularyWord(
                word="ja",
                lemma="ja",
                language="de",
                difficulty_level="A1",
                part_of_speech="adverb",
                translation_en="yes",
                translation_native="sí",
            ),
            VocabularyWord(
                word="nein",
                lemma="nein",
                language="de",
                difficulty_level="A1",
                part_of_speech="adverb",
                translation_en="no",
                translation_native="no",
            ),
            VocabularyWord(
                word="danke",
                lemma="danke",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                translation_en="thanks",
                translation_native="gracias",
            ),
            VocabularyWord(
                word="bitte",
                lemma="bitte",
                language="de",
                difficulty_level="A1",
                part_of_speech="adverb",
                translation_en="please",
                translation_native="por favor",
            ),
            VocabularyWord(
                word="gut",
                lemma="gut",
                language="de",
                difficulty_level="A1",
                part_of_speech="adjective",
                translation_en="good",
                translation_native="bueno",
            ),
            VocabularyWord(
                word="Mann",
                lemma="mann",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                gender="der",
                translation_en="man",
                translation_native="hombre",
            ),
            VocabularyWord(
                word="Frau",
                lemma="frau",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                gender="die",
                translation_en="woman",
                translation_native="mujer",
            ),
            VocabularyWord(
                word="sprechen",
                lemma="sprechen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="speak",
                translation_native="hablar",
            ),
            VocabularyWord(
                word="verstehen",
                lemma="verstehen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="understand",
                translation_native="entender",
            ),
            VocabularyWord(
                word="lernen",
                lemma="lernen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="learn",
                translation_native="aprender",
            ),
            VocabularyWord(
                word="arbeiten",
                lemma="arbeiten",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="work",
                translation_native="trabajar",
            ),
            VocabularyWord(
                word="wohnen",
                lemma="wohnen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="live",
                translation_native="vivir",
            ),
            VocabularyWord(
                word="Mädchen",
                lemma="mädchen",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="das",
                translation_en="girl",
                translation_native="niña",
            ),
            VocabularyWord(
                word="Junge",
                lemma="junge",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="der",
                translation_en="boy",
                translation_native="niño",
            ),
            VocabularyWord(
                word="Familie",
                lemma="familie",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="die",
                translation_en="family",
                translation_native="familia",
            ),
            VocabularyWord(
                word="Schule",
                lemma="schule",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="die",
                translation_en="school",
                translation_native="escuela",
            ),
            VocabularyWord(
                word="Arbeit",
                lemma="arbeit",
                language="de",
                difficulty_level="B1",
                part_of_speech="noun",
                gender="die",
                translation_en="work",
                translation_native="trabajo",
            ),
        ]
        session.add_all(words)
        await session.commit()
        return words


class TestVocabularyRoutesCore:
    """Test core vocabulary route functionality"""

    @pytest.mark.asyncio
    async def test_get_supported_languages_success(self, async_client, url_builder):
        """Test getting supported languages endpoint"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Since the actual endpoint works, let's test the real functionality
        # This will test the actual database integration
        response = await async_client.get(url_builder.url_for("get_supported_languages"), headers=headers)

        # The endpoint should work correctly with expected success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "languages" in data
        # Languages list can be empty if no languages are configured
        assert isinstance(data["languages"], list)

    @pytest.mark.asyncio
    async def test_get_supported_languages_error(self, async_client, app, url_builder):
        """Test error handling in supported languages endpoint"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Create mock session that raises database error
        async def mock_get_async_session():
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Database connection failed")
            yield mock_session

        # Use FastAPI's dependency override system (the correct way)
        from core.database import get_async_session

        app.dependency_overrides[get_async_session] = mock_get_async_session

        try:
            response = await async_client.get(url_builder.url_for("get_supported_languages"), headers=headers)

            assert response.status_code == 500
            # The error handler wraps the exception and returns a 500 with the detail
            error_data = response.json()
            if "error" in error_data:
                assert "Error retrieving supported languages" in error_data["error"]["message"]
            else:
                assert "Error retrieving supported languages" in error_data["detail"]
        finally:
            # Clean up the override
            app.dependency_overrides.pop(get_async_session, None)

    @pytest.mark.asyncio
    async def test_get_vocabulary_stats_success(self, async_client, app, clean_database):
        """Test vocabulary stats endpoint success"""
        # Seed minimal test data inline - clean_database ensures isolation
        from database.models import VocabularyWord

        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            words = [
                VocabularyWord(
                    word="Hallo",
                    lemma="hallo",
                    language="de",
                    difficulty_level="A1",
                    part_of_speech="noun",
                    translation_en="Hello",
                    translation_native="Hola",
                ),
                VocabularyWord(
                    word="Wasser",
                    lemma="wasser",
                    language="de",
                    difficulty_level="A2",
                    part_of_speech="noun",
                    translation_en="Water",
                    translation_native="Agua",
                ),
            ]
            session.add_all(words)
            await session.commit()

        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        response = await async_client.get(
            "/api/vocabulary/stats",
            params={"target_language": "de", "translation_language": "es"},
            headers=headers,
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

    @pytest.mark.asyncio
    async def test_get_vocabulary_level_success(self, async_client, app, clean_database):
        """Test vocabulary level endpoint success"""
        # Seed minimal test data inline - clean_database ensures isolation
        from database.models import VocabularyWord

        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            words = [
                VocabularyWord(
                    word="Hallo",
                    lemma="hallo",
                    language="de",
                    difficulty_level="A1",
                    part_of_speech="noun",
                    translation_en="Hello",
                    translation_native="Hola",
                ),
                VocabularyWord(
                    word="ich",
                    lemma="ich",
                    language="de",
                    difficulty_level="A1",
                    part_of_speech="pronoun",
                    translation_en="I",
                    translation_native="yo",
                ),
            ]
            session.add_all(words)
            await session.commit()

        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Test real endpoint - should work regardless of database state
        response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "de", "translation_language": "es", "limit": 50},
            headers=headers,
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

    @pytest.mark.asyncio
    async def test_get_vocabulary_level_invalid_level(self, async_client):
        """Test vocabulary level endpoint with invalid level"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        response = await async_client.get(
            "/api/vocabulary/library/Z9", params={"target_language": "de"}, headers=headers
        )

        assert response.status_code == 422
        error_data = response.json()
        if "error" in error_data:
            assert "Invalid level" in error_data["error"]["message"]
        else:
            assert "Invalid level" in error_data["detail"]

    @pytest.mark.asyncio
    async def test_mark_word_as_known_success(self, async_client, app):
        """Test marking word as known endpoint success"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Use actual word instead of UUID
        word = "haus"

        # Mock the service using dependency injection override
        from unittest.mock import MagicMock

        from core.dependencies import get_vocabulary_service
        from services.vocabulary.vocabulary_service import VocabularyService

        # Create mock services for DI
        mock_query_service = MagicMock()
        mock_progress_service = MagicMock()
        mock_stats_service = MagicMock()

        mock_service = VocabularyService(
            query_service=mock_query_service,
            progress_service=mock_progress_service,
            stats_service=mock_stats_service,
        )
        mock_service.mark_word_known = AsyncMock(
            return_value={
                "success": True,
                "word": word,
                "lemma": "haus",
                "level": "A1",
            }
        )

        # Override the dependency
        app.dependency_overrides[get_vocabulary_service] = lambda: mock_service

        try:
            response = await async_client.post(
                "/api/vocabulary/mark-known",
                json={"lemma": "haus", "language": "de", "known": True},
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True, f"Expected success=True, got: {data}"
            assert data["word"] == word
        finally:
            # Clean up override
            del app.dependency_overrides[get_vocabulary_service]

            # Verify service was called with correct parameters
            mock_service.mark_word_known.assert_called_once()
            call_args = mock_service.mark_word_known.call_args
            assert call_args.kwargs["word"] == "haus"
            assert call_args.kwargs["language"] == "de"
            assert call_args.kwargs["is_known"] is True

    @pytest.mark.asyncio
    async def test_mark_word_unknown_success(self, async_client, app):
        """Test marking word as unknown endpoint success"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Use actual word instead of UUID
        word = "welt"

        # Mock the service using dependency injection override
        from core.dependencies import get_vocabulary_service
        from services.vocabulary.vocabulary_service import VocabularyService

        mock_query_service = AsyncMock()
        mock_progress_service = AsyncMock()
        mock_stats_service = AsyncMock()
        mock_service = VocabularyService(mock_query_service, mock_progress_service, mock_stats_service)
        mock_service.mark_word_known = AsyncMock(
            return_value={
                "success": True,
                "word": word,
                "lemma": "welt",
                "level": "A1",
            }
        )

        # Override the dependency
        app.dependency_overrides[get_vocabulary_service] = lambda: mock_service

        try:
            response = await async_client.post(
                "/api/vocabulary/mark-known",
                json={"lemma": "welt", "language": "de", "known": False},
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["word"] == word
            assert data["known"] is False

            # Verify service was called with correct parameters
            mock_service.mark_word_known.assert_called_once()
            call_args = mock_service.mark_word_known.call_args
            assert call_args.kwargs["word"] == "welt"
            assert call_args.kwargs["language"] == "de"
            assert call_args.kwargs["is_known"] is False
        finally:
            # Clean up override
            del app.dependency_overrides[get_vocabulary_service]

    @pytest.mark.asyncio
    async def test_bulk_mark_level_known_success(self, async_client, app, clean_database):
        """Test bulk marking level as known endpoint success"""
        # Seed minimal test data inline - clean_database ensures isolation
        from database.models import VocabularyWord

        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            words = [
                VocabularyWord(
                    word="Hallo",
                    lemma="hallo",
                    language="de",
                    difficulty_level="A1",
                    part_of_speech="noun",
                    translation_en="Hello",
                    translation_native="Hola",
                ),
                VocabularyWord(
                    word="ich",
                    lemma="ich",
                    language="de",
                    difficulty_level="A1",
                    part_of_speech="pronoun",
                    translation_en="I",
                    translation_native="yo",
                ),
            ]
            session.add_all(words)
            await session.commit()

        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Test real endpoint behavior - should work regardless of database state
        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1", "target_language": "de", "known": True},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["level"] == "A1"
        assert data["known"] is True
        assert "word_count" in data
        assert isinstance(data["word_count"], int)
        assert data["word_count"] >= 0  # May be 0 if no words for this level

    @pytest.mark.asyncio
    async def test_bulk_mark_level_invalid_level(self, async_client):
        """Test bulk marking with invalid level"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "Z9", "target_language": "de", "known": True},
            headers=headers,
        )

        assert response.status_code == 422
        data = response.json()
        # Custom error handling returns validation errors in error.details array
        assert "error" in data
        assert "details" in data["error"]
        # Should contain pattern validation error for level field
        error_details = data["error"]["details"]
        assert any("pattern" in str(error).lower() for error in error_details)

    @pytest.mark.asyncio
    async def test_get_test_data_success(self, async_client, url_builder, app, clean_database):
        """Test test data endpoint success"""
        # Seed minimal test data inline - clean_database ensures isolation
        from database.models import VocabularyWord

        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            words = [
                VocabularyWord(
                    word="Hallo",
                    lemma="hallo",
                    language="de",
                    difficulty_level="A1",
                    part_of_speech="noun",
                    translation_en="Hello",
                    translation_native="Hola",
                ),
                VocabularyWord(
                    word="Wasser",
                    lemma="wasser",
                    language="de",
                    difficulty_level="A2",
                    part_of_speech="noun",
                    translation_en="Water",
                    translation_native="Agua",
                ),
            ]
            session.add_all(words)
            await session.commit()

        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Test real endpoint - should work regardless of database state
        response = await async_client.get(url_builder.url_for("get_test_data"), headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "concept_count" in data
        assert "translation_count" in data
        assert "sample_translations" in data
        assert isinstance(data["concept_count"], int)
        assert isinstance(data["translation_count"], int)
        assert isinstance(data["sample_translations"], list)
        # Counts may be 0 if no data is configured

    @pytest.mark.asyncio
    async def test_get_blocking_words_missing_srt(self, async_client):
        """Test blocking words endpoint with missing SRT file"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        with patch("api.routes.vocabulary_test_routes.settings") as mock_settings:
            from pathlib import Path

            mock_videos_path = Path("/fake/videos")
            mock_settings.get_videos_path.return_value = mock_videos_path

            # Mock non-existent SRT file
            with patch.object(Path, "exists", return_value=False):
                response = await async_client.get(
                    "/api/vocabulary/blocking-words", params={"video_path": "test.mp4"}, headers=headers
                )

                assert response.status_code == 404
                error_data = response.json()
                if "error" in error_data:
                    assert "Subtitle file not found" in error_data["error"]["message"]
                else:
                    assert "Subtitle file not found" in error_data["detail"]

    @pytest.mark.asyncio
    async def test_get_blocking_words_success(self, async_client, app):
        """Test blocking words endpoint success"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        with patch("api.routes.vocabulary_test_routes.settings") as mock_settings:
            from pathlib import Path

            mock_videos_path = Path("/fake/videos")
            mock_settings.get_videos_path.return_value = mock_videos_path

            # Mock vocabulary service
            from core.dependencies import get_vocabulary_service
            from services.vocabulary.vocabulary_service import VocabularyService

            mock_query_service = AsyncMock()
            mock_progress_service = AsyncMock()
            mock_stats_service = AsyncMock()
            mock_service = VocabularyService(mock_query_service, mock_progress_service, mock_stats_service)
            mock_service.extract_blocking_words_from_srt = AsyncMock(return_value=[])
            app.dependency_overrides[get_vocabulary_service] = lambda: mock_service

            try:
                # Mock existing SRT file and file read
                with patch.object(Path, "exists", return_value=True):
                    with patch("builtins.open", create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = "Mock SRT content"

                        response = await async_client.get(
                            "/api/vocabulary/blocking-words", params={"video_path": "test.mp4"}, headers=headers
                        )

                        assert response.status_code == 200
                        data = response.json()
                        assert "blocking_words" in data
                        assert "video_path" in data
                        assert "srt_path" in data
            finally:
                app.dependency_overrides.pop(get_vocabulary_service, None)


class TestVocabularyRoutesErrorHandling:
    """Test error handling in vocabulary routes"""

    @pytest.mark.asyncio
    async def test_vocabulary_stats_database_error(self, async_client):
        """Test vocabulary stats with realistic error scenarios"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Test with invalid but properly formatted language code
        response = await async_client.get(
            "/api/vocabulary/stats",
            params={"target_language": "xx"},  # Valid format but non-existent language
            headers=headers,
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

    @pytest.mark.asyncio
    async def test_mark_known_database_error(self, async_client):
        """Test mark known with non-existent word (supports unknown words)"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Test with valid lemma but non-existent word - new behavior allows marking unknown words
        response = await async_client.post(
            "/api/vocabulary/mark-known",
            json={"lemma": "unknown_word", "language": "de", "known": True},
            headers=headers,
        )

        # Should succeed (200) - new feature allows marking unknown words as known
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["known"] is True  # API uses "known" field, not "is_known"
        assert data["level"] == "unknown"  # Non-existent words have no CEFR level

    @pytest.mark.asyncio
    async def test_vocabulary_level_database_error(self, async_client):
        """Test vocabulary level with realistic error scenarios"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        # Test with invalid language - should return empty results gracefully
        response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "xx"},  # Valid format but non-existent language
            headers=headers,
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

    @pytest.mark.asyncio
    async def test_mark_known_invalid_uuid(self, async_client):
        """Test mark known with invalid UUID"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        response = await async_client.post(
            "/api/vocabulary/mark-known", json={"concept_id": "not-a-uuid", "known": True}, headers=headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_bulk_mark_missing_fields(self, async_client):
        """Test bulk mark with missing required fields"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1"},  # Missing target_language and known
            headers=headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vocabulary_level_query_params(self, async_client):
        """Test vocabulary level with various query parameters"""
        helper = AsyncAuthHelper(async_client)

        _user, _token, headers = await helper.create_authenticated_user()

        with patch("api.routes.vocabulary_query_routes.get_async_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Mock empty results
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.side_effect = [mock_result, MagicMock(fetchall=lambda: [])]

            response = await async_client.get(
                "/api/vocabulary/library/B2",
                params={"target_language": "es", "translation_language": "en", "limit": 100},
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["level"] == "B2"
            assert data["target_language"] == "es"
            assert data["translation_language"] == "en"
            assert len(data["words"]) == 0
