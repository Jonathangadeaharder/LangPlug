"""
Test suite for ChunkTranscriptionService
Tests audio extraction and transcription for video chunks
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.processing.chunk_transcription_service import ChunkTranscriptionError, ChunkTranscriptionService


class TestChunkTranscriptionServiceInitialization:
    """Test service initialization"""

    def test_initialization(self):
        """Test service initializes successfully"""
        service = ChunkTranscriptionService()
        assert service is not None


class TestFormatSrtTimestamp:
    """Test SRT timestamp formatting"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    def test_format_srt_timestamp_zero(self, service):
        """Test formatting timestamp at zero"""
        result = service._format_srt_timestamp(0.0)
        assert result == "00:00:00,000"

    def test_format_srt_timestamp_seconds(self, service):
        """Test formatting timestamp with seconds"""
        result = service._format_srt_timestamp(45.5)
        assert result == "00:00:45,500"

    def test_format_srt_timestamp_minutes(self, service):
        """Test formatting timestamp with minutes"""
        result = service._format_srt_timestamp(125.250)
        assert result == "00:02:05,250"

    def test_format_srt_timestamp_hours(self, service):
        """Test formatting timestamp with hours"""
        result = service._format_srt_timestamp(3725.123)
        assert result == "01:02:05,123"

    def test_format_srt_timestamp_milliseconds(self, service):
        """Test formatting with precise milliseconds"""
        result = service._format_srt_timestamp(10.999)
        assert result == "00:00:10,999"


class TestCreateChunkSrt:
    """Test SRT file creation"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    def test_create_chunk_srt_success(self, service, tmp_path):
        """Test successful SRT file creation"""
        output_path = tmp_path / "test.srt"
        text = "Hello world, this is a test."

        service._create_chunk_srt(text, output_path, 0.0, 30.0)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "1\n" in content
        assert "00:00:00,000 --> 00:00:30,000" in content
        assert "Hello world, this is a test." in content

    def test_create_chunk_srt_with_whitespace(self, service, tmp_path):
        """Test SRT creation strips whitespace"""
        output_path = tmp_path / "test.srt"
        text = "  \n  Hello world  \n  "

        service._create_chunk_srt(text, output_path, 0.0, 5.0)

        content = output_path.read_text(encoding="utf-8")
        assert "Hello world" in content
        assert "  \n  " not in content.split("Hello world")[0]

    def test_create_chunk_srt_with_offset(self, service, tmp_path):
        """Test SRT creation with time offset"""
        output_path = tmp_path / "test.srt"
        text = "Test content"

        service._create_chunk_srt(text, output_path, 10.5, 15.0)

        content = output_path.read_text(encoding="utf-8")
        assert "00:00:10,500 --> 00:00:25,500" in content

    def test_create_chunk_srt_file_error(self, service):
        """Test SRT creation handles file errors"""
        output_path = Path("/nonexistent/directory/test.srt")
        text = "Test content"

        with pytest.raises(ChunkTranscriptionError, match="SRT creation failed"):
            service._create_chunk_srt(text, output_path, 0.0, 30.0)


class TestFindMatchingSrtFile:
    """Test finding matching SRT files"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    def test_find_matching_srt_file_exact_match(self, service, tmp_path):
        """Test finding SRT with exact name match"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        srt_file = tmp_path / "video.srt"
        srt_file.touch()

        result = service.find_matching_srt_file(video_file)

        assert result == str(srt_file)

    def test_find_matching_srt_file_language_suffix(self, service, tmp_path):
        """Test finding SRT with language suffix"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        srt_file = tmp_path / "video.de.srt"
        srt_file.touch()

        result = service.find_matching_srt_file(video_file)

        assert result == str(srt_file)

    def test_find_matching_srt_file_english_suffix(self, service, tmp_path):
        """Test finding SRT with English suffix"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        srt_file = tmp_path / "video.en.srt"
        srt_file.touch()

        result = service.find_matching_srt_file(video_file)

        assert result == str(srt_file)

    def test_find_matching_srt_file_subtitles_suffix(self, service, tmp_path):
        """Test finding SRT with _subtitles suffix"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        srt_file = tmp_path / "video_subtitles.srt"
        srt_file.touch()

        result = service.find_matching_srt_file(video_file)

        assert result == str(srt_file)

    def test_find_matching_srt_file_not_found(self, service, tmp_path):
        """Test returns default path when no SRT found"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        result = service.find_matching_srt_file(video_file)

        assert result == str(tmp_path / "video.srt")

    def test_find_matching_srt_file_priority(self, service, tmp_path):
        """Test SRT file priority when multiple exist"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        # Create multiple SRT files
        (tmp_path / "video.srt").touch()
        (tmp_path / "video.de.srt").touch()

        result = service.find_matching_srt_file(video_file)

        # Should return the first match (video.srt)
        assert result == str(tmp_path / "video.srt")


class TestCleanupTempAudioFile:
    """Test temporary audio file cleanup"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    def test_cleanup_temp_audio_file_success(self, service, tmp_path):
        """Test successful cleanup of temp audio file"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio_temp.wav"
        audio_file.touch()

        service.cleanup_temp_audio_file(audio_file, video_file)

        assert not audio_file.exists()
        assert video_file.exists()

    def test_cleanup_temp_audio_file_preserves_video(self, service, tmp_path):
        """Test cleanup doesn't delete video file"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        # Audio file same as video file
        service.cleanup_temp_audio_file(video_file, video_file)

        assert video_file.exists()

    def test_cleanup_temp_audio_file_already_deleted(self, service, tmp_path):
        """Test cleanup handles already deleted file"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio_temp.wav"
        # Don't create the file

        # Should not raise error
        service.cleanup_temp_audio_file(audio_file, video_file)

    def test_cleanup_temp_audio_file_permission_error(self, service, tmp_path):
        """Test cleanup handles permission errors gracefully"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio_temp.wav"
        audio_file.touch()

        # Mock unlink to raise permission error
        with patch.object(Path, "unlink", side_effect=PermissionError("Access denied")):
            # Should not raise, just log warning
            service.cleanup_temp_audio_file(audio_file, video_file)


class TestExtractAudioChunkEdgeCases:
    """Test audio extraction edge cases and error handling"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    @pytest.mark.anyio
    async def test_extract_audio_chunk_ffmpeg_not_found(self, service, tmp_path):
        """Test fallback when ffmpeg not found"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("ffmpeg not found")):
            result = await service.extract_audio_chunk(task_id, task_progress, video_file, 0.0, 10.0)

        # Should return video file as fallback
        assert result == video_file

    @pytest.mark.anyio
    async def test_extract_audio_chunk_timeout(self, service, tmp_path):
        """Test ffmpeg timeout handling"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock process that times out
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=TimeoutError())
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(ChunkTranscriptionError, match="timed out"):
                await service.extract_audio_chunk(task_id, task_progress, video_file, 0.0, 10.0)

        mock_process.kill.assert_called_once()


class TestTranscribeChunkEdgeCases:
    """Test transcription edge cases"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    @pytest.mark.anyio
    async def test_transcribe_chunk_service_not_available(self, service, tmp_path):
        """Test handling when transcription service unavailable"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        with patch("core.service_dependencies.get_transcription_service", return_value=None):
            with pytest.raises(ChunkTranscriptionError, match="not available"):
                await service.transcribe_chunk(task_id, task_progress, video_file, audio_file, {"target": "de"})

    @pytest.mark.anyio
    async def test_transcribe_chunk_fallback_mode(self, service, tmp_path):
        """Test transcription fallback when audio equals video"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        srt_file = tmp_path / "video.srt"
        srt_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        mock_service = Mock()
        with patch("core.service_dependencies.get_transcription_service", return_value=mock_service):
            result = await service.transcribe_chunk(
                task_id,
                task_progress,
                video_file,
                video_file,  # Same as video = fallback mode
                {"target": "de"},
            )

        assert result == str(srt_file)

    @pytest.mark.anyio
    async def test_transcribe_chunk_text_result(self, service, tmp_path):
        """Test transcription with text object result"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service returning object with .text attribute
        mock_service = Mock()
        mock_result = Mock()
        mock_result.text = "Transcribed text content"
        mock_service.transcribe_audio = AsyncMock(return_value=mock_result)

        with patch("core.service_dependencies.get_transcription_service", return_value=mock_service):
            result = await service.transcribe_chunk(task_id, task_progress, video_file, audio_file, {"target": "de"})

        assert result == str(video_file.with_suffix(".srt"))

    @pytest.mark.anyio
    async def test_transcribe_chunk_string_result(self, service, tmp_path):
        """Test transcription with string result"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service returning string
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value="Direct string transcription")

        with patch("core.service_dependencies.get_transcription_service", return_value=mock_service):
            result = await service.transcribe_chunk(task_id, task_progress, video_file, audio_file, {"target": "de"})

        assert result == str(video_file.with_suffix(".srt"))

    @pytest.mark.anyio
    async def test_transcribe_chunk_error_with_fallback(self, service, tmp_path):
        """Test transcription error falls back to existing SRT"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        # Create existing SRT file
        srt_file = tmp_path / "video.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:05,000\nExisting content\n\n")

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service that raises error
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=Exception("Transcription failed"))

        with patch("core.service_dependencies.get_transcription_service", return_value=mock_service):
            result = await service.transcribe_chunk(task_id, task_progress, video_file, audio_file, {"target": "de"})

        # Should return existing SRT as fallback
        assert result == str(srt_file)

    @pytest.mark.anyio
    async def test_transcribe_chunk_error_no_fallback(self, service, tmp_path):
        """Test transcription error without fallback SRT"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service that raises error
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=Exception("Transcription failed"))

        with patch("core.service_dependencies.get_transcription_service", return_value=mock_service):
            with pytest.raises(ChunkTranscriptionError, match="no fallback available"):
                await service.transcribe_chunk(task_id, task_progress, video_file, audio_file, {"target": "de"})
