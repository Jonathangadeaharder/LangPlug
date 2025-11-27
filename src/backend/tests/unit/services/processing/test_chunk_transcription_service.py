"""
Test suite for ChunkTranscriptionService
Tests audio extraction and transcription for video chunks
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.processing.chunk_transcription_service import ChunkTranscriptionError, ChunkTranscriptionService
from services.transcriptionservice.interface import TranscriptionResult, TranscriptionSegment


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


class TestCreateSrtFromSegments:
    """Test SRT creation from transcription segments"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    def test_create_srt_from_segments_success(self, service, tmp_path):
        """Test creating SRT from Whisper segments"""
        output_path = tmp_path / "test.srt"

        segments = [
            TranscriptionSegment(start_time=0.0, end_time=2.5, text="Hello world"),
            TranscriptionSegment(start_time=2.5, end_time=5.0, text="This is a test"),
            TranscriptionSegment(start_time=5.0, end_time=8.0, text="Of segment creation"),
        ]

        service._create_srt_from_segments(segments, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Check segments are present
        assert "Hello world" in content
        assert "This is a test" in content
        assert "Of segment creation" in content

        # Check timing
        assert "00:00:00,000 --> 00:00:02,500" in content
        assert "00:00:02,500 --> 00:00:05,000" in content

    def test_create_srt_from_empty_segments(self, service, tmp_path):
        """Test creating SRT from empty segments list"""
        output_path = tmp_path / "test.srt"
        segments = []

        service._create_srt_from_segments(segments, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert content.strip() == ""


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

    def test_find_matching_srt_file_not_found(self, service, tmp_path):
        """Test returns default path when no SRT found"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        result = service.find_matching_srt_file(video_file)

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


class TestExtractAudioChunk:
    """Test audio extraction"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    @pytest.mark.asyncio
    async def test_extract_audio_chunk_ffmpeg_not_found(self, service, tmp_path):
        """Test error when ffmpeg not found"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("ffmpeg not found")):
            with pytest.raises(ChunkTranscriptionError, match="FFmpeg is not installed"):
                await service.extract_audio_chunk(task_id, task_progress, video_file, 0.0, 10.0)

    @pytest.mark.asyncio
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


class TestTranscribeChunk:
    """Test transcription"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    @pytest.mark.asyncio
    async def test_transcribe_chunk_service_not_available(self, service, tmp_path):
        """Test handling when transcription service unavailable"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        with patch("core.dependencies.get_transcription_service", return_value=None):
            with pytest.raises(ChunkTranscriptionError, match="not available"):
                await service.transcribe_chunk(
                    task_id, task_progress, video_file, audio_file, {"target": "de"}, 0.0, 30.0
                )

    @pytest.mark.asyncio
    async def test_transcribe_chunk_no_audio_file(self, service, tmp_path):
        """Test error when audio file equals video file (no extraction)"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        mock_service = Mock()
        with patch("core.dependencies.get_transcription_service", return_value=mock_service):
            with pytest.raises(ChunkTranscriptionError, match="Audio extraction did not produce a separate audio file"):
                await service.transcribe_chunk(
                    task_id, task_progress, video_file, video_file, {"target": "de"}, 0.0, 30.0
                )

    @pytest.mark.asyncio
    async def test_transcribe_chunk_with_segments(self, service, tmp_path):
        """Test transcription with segment-based result"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service returning segments
        mock_service = Mock()
        mock_result = TranscriptionResult(
            full_text="Hello world. This is a test.",
            segments=[
                TranscriptionSegment(start_time=0.0, end_time=2.0, text="Hello world."),
                TranscriptionSegment(start_time=2.0, end_time=4.5, text="This is a test."),
            ],
            language="de",
        )

        with patch("core.dependencies.get_transcription_service", return_value=mock_service):
            with patch("asyncio.to_thread", return_value=mock_result):
                result = await service.transcribe_chunk(
                    task_id, task_progress, video_file, audio_file, {"target": "de"}, 0.0, 30.0
                )

        assert result == str(video_file.with_suffix(".srt"))
        assert Path(result).exists()

        # Verify SRT content has segments
        content = Path(result).read_text()
        assert "Hello world" in content
        assert "This is a test" in content

    @pytest.mark.asyncio
    async def test_transcribe_chunk_fallback_single_segment(self, service, tmp_path):
        """Test transcription fallback to single segment when no segments"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service returning only full_text
        mock_service = Mock()
        mock_result = TranscriptionResult(
            full_text="Single segment text",
            segments=[],
            language="de",
        )

        with patch("core.dependencies.get_transcription_service", return_value=mock_service):
            with patch("asyncio.to_thread", return_value=mock_result):
                result = await service.transcribe_chunk(
                    task_id, task_progress, video_file, audio_file, {"target": "de"}, 0.0, 30.0
                )

        assert result == str(video_file.with_suffix(".srt"))
        assert Path(result).exists()

    @pytest.mark.asyncio
    async def test_transcribe_chunk_error_no_fallback(self, service, tmp_path):
        """Test transcription error without fallback"""
        video_file = tmp_path / "video.mp4"
        video_file.touch()

        audio_file = tmp_path / "audio.wav"
        audio_file.touch()

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=0, current_step="", message="")}

        # Mock transcription service that raises error
        mock_service = Mock()

        with patch("core.dependencies.get_transcription_service", return_value=mock_service):
            with patch("asyncio.to_thread", side_effect=Exception("Transcription failed")):
                with pytest.raises(ChunkTranscriptionError, match="Chunk transcription failed"):
                    await service.transcribe_chunk(
                        task_id, task_progress, video_file, audio_file, {"target": "de"}, 0.0, 30.0
                    )


class TestProgressSimulation:
    """Test progress simulation during transcription"""

    @pytest.fixture
    def service(self):
        return ChunkTranscriptionService()

    @pytest.mark.asyncio
    async def test_progress_updates_during_transcription(self, service):
        """Test that progress is updated during simulated transcription wait."""
        import asyncio

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=5, current_step="", message="")}
        stop_event = asyncio.Event()
        
        # Start progress simulation for a 60-second audio (estimated ~12s transcription)
        progress_task = asyncio.create_task(
            service._simulate_transcription_progress(task_id, task_progress, 60.0, stop_event)
        )
        
        # Wait a bit for progress to update
        await asyncio.sleep(2.5)
        
        # Stop simulation
        stop_event.set()
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass
        
        # Progress should have increased from initial 5%
        assert task_progress[task_id].progress > 5, "Progress should increase during transcription"
        # Progress should be less than 35% (end of transcription phase)
        assert task_progress[task_id].progress < 35, "Progress should not exceed transcription phase end"
        # Message should include elapsed time
        assert "elapsed" in task_progress[task_id].message.lower(), "Message should show elapsed time"

    @pytest.mark.asyncio
    async def test_progress_caps_at_95_percent_of_target(self, service):
        """Test that progress caps at 95% of target range to leave room for completion."""
        import asyncio

        task_id = "test_task"
        task_progress = {task_id: Mock(progress=5, current_step="", message="")}
        stop_event = asyncio.Event()
        
        # Start progress simulation for very short audio (2s -> estimated 0.4s transcription)
        progress_task = asyncio.create_task(
            service._simulate_transcription_progress(task_id, task_progress, 2.0, stop_event)
        )
        
        # Wait longer than estimated time
        await asyncio.sleep(5.0)
        
        # Stop simulation
        stop_event.set()
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass
        
        # Progress should not exceed ~33.5% (5% + 0.95 * 30% = 33.5%)
        assert task_progress[task_id].progress <= 34, "Progress should cap at ~95% of target range"
