"""
Test suite for ChunkUtilities
Tests utility functions for chunk processing including file management and user operations
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

import pytest

from api.models.processing import ProcessingStatus
from services.processing.chunk_utilities import ChunkUtilities, ChunkUtilitiesError


class TestChunkUtilitiesInitialization:
    """Test service initialization"""

    def test_initialization(self):
        """Test service initializes with database session"""
        mock_session = AsyncMock()

        service = ChunkUtilities(mock_session)

        assert service.db_session == mock_session


class TestResolveVideoPath:
    """Test video path resolution"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_resolve_video_path_absolute(self, service):
        """Test resolving absolute path"""
        absolute_path = "/home/user/videos/video.mp4"

        result = service.resolve_video_path(absolute_path)

        assert result == Path(absolute_path)

    def test_resolve_video_path_relative(self, service):
        """Test resolving relative path"""
        with patch("services.processing.chunk_utilities.settings") as mock_settings:
            mock_settings.get_videos_path.return_value = Path("/videos")
            relative_path = "subfolder/video.mp4"

            result = service.resolve_video_path(relative_path)

            assert result == Path("/videos/subfolder/video.mp4")
            mock_settings.get_videos_path.assert_called_once()


class TestGetAuthenticatedUser:
    """Test user authentication"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    @pytest.mark.anyio
    async def test_get_authenticated_user_success(self, service):
        """Test successful user authentication"""
        # Arrange
        mock_user = Mock(id=1, username="testuser")
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user

        service.db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.get_authenticated_user(1, None)

        # Assert
        assert result == mock_user
        assert result.username == "testuser"

    @pytest.mark.anyio
    async def test_get_authenticated_user_not_found(self, service):
        """Test user not found raises error"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        service.db_session.execute = AsyncMock(return_value=mock_result)

        # Act & Assert
        with pytest.raises(ChunkUtilitiesError, match="User not found"):
            await service.get_authenticated_user(999, None)

    @pytest.mark.anyio
    async def test_get_authenticated_user_with_session_token(self, service):
        """Test authentication with session token"""
        # Arrange
        mock_user = Mock(id=1, username="testuser")
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user

        service.db_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await service.get_authenticated_user(1, "token123456789")

        # Assert
        assert result == mock_user

    @pytest.mark.anyio
    async def test_get_authenticated_user_database_error(self, service):
        """Test database error during authentication"""
        # Arrange
        service.db_session.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        # Act & Assert
        with pytest.raises(ChunkUtilitiesError, match="Authentication failed"):
            await service.get_authenticated_user(1, None)


class TestNormalizeUserIdentifier:
    """Test user identifier normalization"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_normalize_user_identifier_uuid_string(self, service):
        """Test normalizing UUID string"""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        result = service._normalize_user_identifier(uuid_str)

        assert isinstance(result, str)
        assert result == uuid_str

    def test_normalize_user_identifier_int_string(self, service):
        """Test normalizing integer string"""
        result = service._normalize_user_identifier("42")

        assert result == 42
        assert isinstance(result, int)

    def test_normalize_user_identifier_regular_string(self, service):
        """Test normalizing regular string"""
        result = service._normalize_user_identifier("username")

        assert result == "username"
        assert isinstance(result, str)

    def test_normalize_user_identifier_int(self, service):
        """Test normalizing integer"""
        result = service._normalize_user_identifier(42)

        assert result == 42
        assert isinstance(result, int)

    def test_normalize_user_identifier_uuid(self, service):
        """Test normalizing UUID object"""
        uuid_obj = UUID("123e4567-e89b-12d3-a456-426614174000")

        result = service._normalize_user_identifier(uuid_obj)

        assert result == uuid_obj


class TestLoadUserLanguagePreferences:
    """Test loading user language preferences"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_load_user_language_preferences(self, service):
        """Test loading language preferences for user"""
        mock_user = Mock(id=1)

        with patch("services.processing.chunk_utilities.load_language_preferences") as mock_load:
            with patch("services.processing.chunk_utilities.resolve_language_runtime_settings") as mock_resolve:
                mock_load.return_value = {"target": "de", "native": "en"}
                mock_resolve.return_value = {"target": "de", "native": "en", "level": "A1"}

                result = service.load_user_language_preferences(mock_user)

                assert result["target"] == "de"
                assert result["native"] == "en"
                assert result["level"] == "A1"
                mock_load.assert_called_once_with("1")
                mock_resolve.assert_called_once()


class TestCleanupOldChunkFiles:
    """Test cleanup of old chunk files"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_cleanup_old_chunk_files_success(self, service, tmp_path):
        """Test successful cleanup of old chunk files"""
        # Arrange
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        old_chunk = tmp_path / "video_chunk_0_10.srt"
        old_chunk.touch()

        # Act
        service.cleanup_old_chunk_files(video_file, 0, 10)

        # Assert - old chunk should be deleted
        assert video_file.exists()
        assert not old_chunk.exists()

    def test_cleanup_old_chunk_files_no_files(self, service, tmp_path):
        """Test cleanup when no old files exist"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        # Act - should not raise error
        service.cleanup_old_chunk_files(video_file, 0, 10)

        assert video_file.exists()

    def test_cleanup_old_chunk_files_preserves_video(self, service, tmp_path):
        """Test cleanup preserves the video file"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        # Act
        service.cleanup_old_chunk_files(video_file, 0, 10)

        # Assert - video file should still exist
        assert video_file.exists()

    def test_cleanup_old_chunk_files_handles_errors(self, service):
        """Test cleanup handles errors gracefully"""
        video_file = Path("/nonexistent/video.mp4")

        # Act - should not raise error
        service.cleanup_old_chunk_files(video_file, 0, 10)


class TestInitializeProgress:
    """Test progress tracking initialization"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_initialize_progress(self, service, tmp_path):
        """Test initializing progress tracking"""
        task_id = "task123"
        task_progress = {}
        video_file = tmp_path / "video.mp4"
        start_time = 0.0
        end_time = 10.5

        service.initialize_progress(task_id, task_progress, video_file, start_time, end_time)

        assert task_id in task_progress
        assert task_progress[task_id].status == "processing"
        assert task_progress[task_id].progress == 0.0
        assert task_progress[task_id].current_step == "Starting chunk processing..."
        assert "video.mp4" in task_progress[task_id].message
        assert "0.0s" in task_progress[task_id].message
        assert "10.5s" in task_progress[task_id].message


class TestCompleteProcessing:
    """Test marking processing as complete"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_complete_processing_without_vocabulary(self, service):
        """Test completing processing without vocabulary"""
        task_id = "task123"
        task_progress = {
            task_id: ProcessingStatus(
                status="processing", progress=50.0, current_step="Processing...", message="Working..."
            )
        }

        service.complete_processing(task_id, task_progress)

        assert task_progress[task_id].status == "completed"
        assert task_progress[task_id].progress == 100.0
        assert task_progress[task_id].current_step == "Chunk processing completed"

    def test_complete_processing_with_vocabulary(self, service):
        """Test completing processing with vocabulary"""
        task_id = "task123"
        task_progress = {
            task_id: ProcessingStatus(
                status="processing", progress=50.0, current_step="Processing...", message="Working..."
            )
        }
        vocabulary = [{"word": "Hallo", "difficulty_level": "A1"}]

        service.complete_processing(task_id, task_progress, vocabulary)

        assert task_progress[task_id].status == "completed"
        assert task_progress[task_id].progress == 100.0
        # Vocabulary gets converted to VocabularyWord Pydantic objects
        assert len(task_progress[task_id].vocabulary) == 1
        assert task_progress[task_id].vocabulary[0].word == "Hallo"
        assert task_progress[task_id].vocabulary[0].difficulty_level == "A1"


class TestHandleError:
    """Test error handling"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_handle_error(self, service):
        """Test handling error in processing"""
        task_id = "task123"
        task_progress = {}
        error = Exception("Test error message")

        service.handle_error(task_id, task_progress, error)

        assert task_id in task_progress
        assert task_progress[task_id].status == "error"
        assert task_progress[task_id].progress == 0.0
        assert task_progress[task_id].current_step == "Processing failed"
        assert "Test error message" in task_progress[task_id].message


class TestDebugEmptyVocabulary:
    """Test debug logging for empty vocabulary"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    def test_debug_empty_vocabulary_with_result(self, service):
        """Test debug logging with filter result"""
        filter_result = {"blocker_words": [], "total_words": 0, "filtered": True}
        srt_file_path = "/path/to/file.srt"

        # Act - should not raise error
        service.debug_empty_vocabulary(filter_result, srt_file_path)

    def test_debug_empty_vocabulary_none_result(self, service):
        """Test debug logging with None result"""
        srt_file_path = "/path/to/file.srt"

        # Act - should not raise error
        service.debug_empty_vocabulary(None, srt_file_path)

    def test_debug_empty_vocabulary_empty_dict(self, service):
        """Test debug logging with empty dictionary"""
        srt_file_path = "/path/to/file.srt"

        # Act - should not raise error
        service.debug_empty_vocabulary({}, srt_file_path)


class TestIntegration:
    """Test integration scenarios"""

    @pytest.fixture
    def service(self):
        return ChunkUtilities(AsyncMock())

    @pytest.mark.anyio
    async def test_full_workflow(self, service, tmp_path):
        """Test complete utility workflow"""
        # Arrange
        task_id = "integration_test"
        task_progress = {}
        video_file = tmp_path / "video.mp4"
        video_file.touch()
        start_time = 0.0
        end_time = 10.0

        mock_user = Mock(id=1, username="testuser")
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        service.db_session.execute = AsyncMock(return_value=mock_result)

        with patch("services.processing.chunk_utilities.load_language_preferences") as mock_load:
            with patch("services.processing.chunk_utilities.resolve_language_runtime_settings") as mock_resolve:
                # load_language_preferences returns (native, target) tuple
                mock_load.return_value = ("en", "de")
                mock_resolve.return_value = {"target": "de", "native": "en"}

                # Act - run through workflow
                service.initialize_progress(task_id, task_progress, video_file, start_time, end_time)
                user = await service.get_authenticated_user(1, None)
                preferences = service.load_user_language_preferences(user)
                service.complete_processing(task_id, task_progress)

                # Assert
                assert user.username == "testuser"
                assert preferences["target"] == "de"
                assert task_progress[task_id].status == "completed"
                assert task_progress[task_id].progress == 100.0
