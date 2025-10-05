"""
Test suite for ChunkProcessingService
Tests video chunk processing orchestration and vocabulary filtering
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from services.processing.chunk_processor import ChunkProcessingService


class TestChunkProcessingServiceInitialization:
    """Test service initialization"""

    def test_initialization(self, mock_db_session):
        """Test service initializes with required components"""
        service = ChunkProcessingService(mock_db_session)

        assert service.db_session == mock_db_session
        assert service.transcription_service is not None
        assert service.translation_service is not None
        assert service.utilities is not None


class TestProcessChunk:
    """Test main chunk processing orchestration"""

    @pytest.fixture
    def service(self, mock_db_session):
        """Create service instance with mocked session"""
        return ChunkProcessingService(mock_db_session)

    @pytest.fixture
    def task_progress(self):
        """Create task progress dictionary"""
        return {}

    @pytest.mark.anyio
    async def test_process_chunk_success_flow(self, service, task_progress):
        """Test successful chunk processing flow"""
        # Arrange
        video_path = "/path/to/video.mp4"
        task_id = "test_task_123"

        # Mock all components
        service.utilities.resolve_video_path = Mock(return_value=Path("/resolved/video.mp4"))
        service.utilities.initialize_progress = Mock()
        service.utilities.get_authenticated_user = AsyncMock(return_value=Mock(id=1))
        service.utilities.load_user_language_preferences = Mock(return_value={"level": "A1", "target": "de"})
        service.utilities.complete_processing = Mock()
        service.utilities.cleanup_old_chunk_files = Mock()

        service.transcription_service.extract_audio_chunk = AsyncMock(return_value="/temp/audio.wav")
        service.transcription_service.transcribe_chunk = AsyncMock(return_value="/temp/subtitles.srt")
        service.transcription_service.find_matching_srt_file = Mock(return_value="/temp/subtitles.srt")
        service.transcription_service.cleanup_temp_audio_file = Mock()

        service._filter_vocabulary = AsyncMock(return_value=[{"word": "test", "difficulty": "A1"}])
        service._generate_filtered_subtitles = AsyncMock(return_value="/temp/filtered.srt")

        service.translation_service.build_translation_segments = AsyncMock(return_value=[])

        # Act
        await service.process_chunk(
            video_path=video_path,
            start_time=0.0,
            end_time=10.0,
            user_id=1,
            task_id=task_id,
            task_progress=task_progress,
            session_token="test_token",
        )

        # Assert - verify orchestration completed successfully
        service.utilities.resolve_video_path.assert_called_once_with(video_path)
        service.utilities.complete_processing.assert_called_once()
        service.transcription_service.cleanup_temp_audio_file.assert_called_once()

    @pytest.mark.anyio
    async def test_process_chunk_error_cleanup(self, service, task_progress):
        """Test cleanup on error"""
        # Arrange
        service.utilities.resolve_video_path = Mock(return_value=Path("/video.mp4"))
        service.utilities.initialize_progress = Mock()
        service.utilities.get_authenticated_user = AsyncMock(side_effect=Exception("Auth failed"))
        service.utilities.handle_error = Mock()
        service.transcription_service.cleanup_temp_audio_file = Mock()

        # Act & Assert
        with pytest.raises(Exception, match="Auth failed"):
            await service.process_chunk(
                video_path="/video.mp4",
                start_time=0.0,
                end_time=10.0,
                user_id=1,
                task_id="test_task",
                task_progress=task_progress,
            )

        # Verify error handling was called
        service.utilities.handle_error.assert_called_once()


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.fixture
    def service(self, mock_db_session):
        return ChunkProcessingService(mock_db_session)

    @pytest.mark.anyio
    async def test_health_check(self, service):
        """Test service health check"""
        # Act
        result = await service.health_check()

        # Assert
        assert result["service"] == "ChunkProcessingService"
        assert result["status"] == "healthy"
        assert "components" in result
        assert result["components"]["transcription"] == "available"


class TestLifecycleMethods:
    """Test service lifecycle methods"""

    @pytest.fixture
    def service(self, mock_db_session):
        return ChunkProcessingService(mock_db_session)

    @pytest.mark.anyio
    async def test_initialize(self, service):
        """Test service initialization"""
        await service.initialize()
        # Should complete without error

    @pytest.mark.anyio
    async def test_cleanup(self, service):
        """Test service cleanup"""
        await service.cleanup()
        # Should complete without error


class TestHandleMethod:
    """Test handler interface implementation"""

    @pytest.fixture
    def service(self, mock_db_session):
        return ChunkProcessingService(mock_db_session)

    @pytest.mark.anyio
    async def test_handle_delegates_to_process_chunk(self, service):
        """Test handle method delegates to process_chunk"""
        # Arrange
        service.process_chunk = AsyncMock()
        task_progress = {}

        # Act
        await service.handle(
            task_id="test_task",
            task_progress=task_progress,
            video_path="/video.mp4",
            start_time=0.0,
            end_time=10.0,
            user_id=1,
        )

        # Assert - process_chunk was called with parameters
        service.process_chunk.assert_called_once()
        call_kwargs = service.process_chunk.call_args.kwargs
        assert call_kwargs["task_id"] == "test_task"
        assert call_kwargs["video_path"] == "/video.mp4"


class TestValidateParameters:
    """Test parameter validation"""

    @pytest.fixture
    def service(self, mock_db_session):
        return ChunkProcessingService(mock_db_session)

    def test_validate_parameters_all_present(self, service):
        """Test validation with all required parameters"""
        # Act
        result = service.validate_parameters(video_path="/video.mp4", start_time=0.0, end_time=10.0, user_id=1)

        # Assert
        assert result is True

    def test_validate_parameters_missing_parameter(self, service):
        """Test validation with missing parameter"""
        # Act
        result = service.validate_parameters(
            video_path="/video.mp4",
            start_time=0.0,
            end_time=10.0,
            # Missing user_id
        )

        # Assert
        assert result is False

    def test_validate_parameters_empty(self, service):
        """Test validation with no parameters"""
        # Act
        service.validate_parameters()

        # Assert
