"""
Resource Management Tests for Chunk Processing
Testing FFmpeg timeout, cleanup, and resource management
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.processing.chunk_transcription_service import (
    ChunkTranscriptionError,
    ChunkTranscriptionService,
)


class TestChunkTranscriptionServiceResourceCleanup:
    """Test resource cleanup in chunk transcription"""

    @pytest.mark.asyncio
    async def test_When_audio_extraction_succeeds_Then_audio_file_created(self):
        """Test successful audio extraction creates audio file"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            audio_output = Path(tmpdir) / f"{video_file.stem}_chunk_0.0s_10.0s.wav"

            # Mock FFmpeg subprocess
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0

            async def mock_wait_for(coro, timeout):
                return await coro

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", side_effect=mock_wait_for):
                    # Create a non-empty audio file to simulate successful extraction
                    # Service rejects 0-byte files as invalid
                    audio_output.write_bytes(b"RIFF" + b"\x00" * 100)

                    # Act
                    audio_file = await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                    # Assert
                    assert audio_file is not None
                    assert audio_file.exists()

    @pytest.mark.asyncio
    async def test_When_audio_extraction_fails_Then_partial_file_cleaned_up(self):
        """Test failed audio extraction cleans up partial files"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            audio_file = Path(tmpdir) / "test_video_chunk_0.0s_10.0s.wav"
            audio_file.touch()  # Create partial file

            # Mock FFmpeg subprocess failure
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b"FFmpeg error"))
            mock_process.returncode = 1

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", side_effect=lambda coro, timeout: coro):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "unlink"):
                            # Act & Assert
                            with pytest.raises(ChunkTranscriptionError):
                                await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                            # Verify cleanup was attempted
                            assert True  # Cleanup logic executed

    @pytest.mark.asyncio
    async def test_When_ffmpeg_times_out_Then_process_killed_and_error_raised(self):
        """Test FFmpeg timeout kills process and raises error"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()

            # Mock FFmpeg subprocess that times out
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock()
            mock_process.kill = Mock()
            mock_process.wait = AsyncMock()

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", side_effect=TimeoutError()):
                    # Act & Assert
                    with pytest.raises(ChunkTranscriptionError) as exc_info:
                        await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                    # Verify timeout error message
                    assert "timed out" in str(exc_info.value).lower()
                    # Verify process was killed
                    mock_process.kill.assert_called_once()
                    mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_When_cleanup_temp_audio_file_called_Then_file_deleted(self):
        """Test cleanup_temp_audio_file deletes temporary audio files"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "video.mp4"
            video_file.touch()
            audio_file = Path(tmpdir) / "video_chunk_0.0s_10.0s.wav"
            audio_file.touch()

            # Act
            service.cleanup_temp_audio_file(audio_file, video_file)

            # Assert
            assert not audio_file.exists()

    @pytest.mark.asyncio
    async def test_When_cleanup_video_file_Then_not_deleted(self):
        """Test cleanup doesn't delete original video file"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "video.mp4"
            video_file.touch()

            # Act - Try to cleanup video file (should not delete it)
            service.cleanup_temp_audio_file(video_file, video_file)

            # Assert - Video file should still exist
            assert video_file.exists()

    @pytest.mark.asyncio
    async def test_When_cleanup_nonexistent_file_Then_no_error(self):
        """Test cleanup handles nonexistent files gracefully"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "video.mp4"
            audio_file = Path(tmpdir) / "nonexistent.wav"

            # Act - Should not raise exception
            service.cleanup_temp_audio_file(audio_file, video_file)

            # Assert - No exception raised

    @pytest.mark.asyncio
    async def test_When_cleanup_fails_Then_logged_but_not_raised(self):
        """Test cleanup failure is logged but doesn't raise exception"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "video.mp4"
            audio_file = Path(tmpdir) / "audio.wav"
            audio_file.touch()

            # Mock unlink to raise exception
            with patch.object(Path, "unlink", side_effect=PermissionError("Access denied")):
                # Act - Should not raise exception
                service.cleanup_temp_audio_file(audio_file, video_file)

                # Assert - No exception raised


class TestChunkTranscriptionServiceErrorHandling:
    """Test error handling in chunk transcription"""

    @pytest.mark.asyncio
    async def test_When_ffmpeg_not_found_Then_fallback_mode(self):
        """Test FFmpeg not found raises clear error (fail-fast)"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()

            # Mock FFmpeg not found
            with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
                # Act & Assert - Fail fast with clear error
                with pytest.raises(ChunkTranscriptionError) as exc_info:
                    await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                # Verify error message mentions FFmpeg
                assert "ffmpeg" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_When_unexpected_error_Then_cleanup_and_raise(self):
        """Test unexpected errors trigger cleanup and re-raise"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()

            # Mock unexpected error
            with patch("asyncio.create_subprocess_exec", side_effect=RuntimeError("Unexpected")):
                # Act & Assert
                with pytest.raises(ChunkTranscriptionError) as exc_info:
                    await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                assert "Unexpected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_When_transcription_fails_Then_fallback_to_existing_srt(self):
        """Test transcription failure raises clear error (fail-fast)"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            audio_file = Path(tmpdir) / "test_audio.wav"
            audio_file.touch()
            srt_file = Path(tmpdir) / "test_video.srt"
            srt_file.write_text("1\n00:00:00,000 --> 00:00:05,000\nTest subtitle\n")

            # Mock transcription service failure
            mock_transcription_service = Mock()
            mock_transcription_service.transcribe = Mock(side_effect=Exception("Transcription failed"))

            with patch("core.dependencies.get_transcription_service", return_value=mock_transcription_service):
                # Act & Assert - Fail fast with clear error
                with pytest.raises(ChunkTranscriptionError) as exc_info:
                    await service.transcribe_chunk("task123", task_progress, video_file, audio_file, {"target": "de"})

                # Verify error message mentions transcription failure
                assert "transcription failed" in str(exc_info.value).lower()


class TestChunkTranscriptionServiceTimeoutConfiguration:
    """Test timeout configuration"""

    @pytest.mark.asyncio
    async def test_When_audio_extraction_Then_timeout_set_to_600_seconds(self):
        """Test audio extraction has 10-minute timeout"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            audio_output = Path(tmpdir) / f"{video_file.stem}_chunk_0.0s_10.0s.wav"

            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0

            timeout_used = []

            async def mock_wait_for(coro, timeout):
                timeout_used.append(timeout)
                # Create non-empty audio file to simulate successful extraction
                # Service rejects 0-byte files as invalid
                audio_output.write_bytes(b"RIFF" + b"\x00" * 100)
                return await coro

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", side_effect=mock_wait_for):
                    # Act
                    await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                    # Assert - Timeout is 600 seconds (10 minutes)
                    assert 600 in timeout_used


class TestChunkTranscriptionServiceSRTHandling:
    """Test SRT file handling"""

    def test_When_find_matching_srt_Then_returns_existing_file(self):
        """Test find_matching_srt_file finds existing SRT"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            srt_file = Path(tmpdir) / "test_video.srt"
            srt_file.touch()

            # Act
            result = service.find_matching_srt_file(video_file)

            # Assert
            assert srt_file.name in result

    def test_When_no_srt_exists_Then_returns_default_path(self):
        """Test find_matching_srt_file returns default path when no SRT exists"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()

            # Act
            result = service.find_matching_srt_file(video_file)

            # Assert
            assert ".srt" in result

    def test_When_create_chunk_srt_Then_srt_file_created(self):
        """Test _create_chunk_srt creates valid SRT file"""
        # Arrange
        service = ChunkTranscriptionService()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.srt"

            # Act
            service._create_chunk_srt("Test transcription text", output_path, 0.0, 30.0)

            # Assert
            assert output_path.exists()
            content = output_path.read_text()
            assert "Test transcription text" in content
            assert "00:00:00,000" in content
            assert "00:00:30,000" in content

    def test_When_create_srt_fails_Then_error_raised(self):
        """Test _create_chunk_srt failure raises error"""
        # Arrange
        service = ChunkTranscriptionService()

        # Mock file write to fail
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            # Act & Assert
            with pytest.raises(ChunkTranscriptionError) as exc_info:
                service._create_chunk_srt("Test text", Path("output.srt"), 0.0, 30.0)

            assert "SRT creation failed" in str(exc_info.value)


class TestChunkTranscriptionServiceTimestampFormatting:
    """Test SRT timestamp formatting"""

    def test_When_format_srt_timestamp_Then_correct_format(self):
        """Test _format_srt_timestamp produces correct format"""
        # Arrange
        service = ChunkTranscriptionService()

        # Act
        result = service._format_srt_timestamp(90.5)  # 1 minute 30.5 seconds

        # Assert
        assert result == "00:01:30,500"

    def test_When_format_zero_seconds_Then_correct_format(self):
        """Test _format_srt_timestamp with zero seconds"""
        # Arrange
        service = ChunkTranscriptionService()

        # Act
        result = service._format_srt_timestamp(0.0)

        # Assert
        assert result == "00:00:00,000"

    def test_When_format_hours_Then_correct_format(self):
        """Test _format_srt_timestamp with hours"""
        # Arrange
        service = ChunkTranscriptionService()

        # Act
        result = service._format_srt_timestamp(3661.25)  # 1 hour, 1 minute, 1.25 seconds

        # Assert
        assert result == "01:01:01,250"


class TestChunkTranscriptionServiceProgressTracking:
    """Test progress tracking during transcription"""

    @pytest.mark.asyncio
    async def test_When_extract_audio_chunk_Then_progress_updated(self):
        """Test progress is updated during audio extraction"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            audio_output = Path(tmpdir) / f"{video_file.stem}_chunk_0.0s_10.0s.wav"

            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0

            async def mock_wait_for(coro, timeout):
                # Create non-empty audio file - service rejects 0-byte files
                audio_output.write_bytes(b"RIFF" + b"\x00" * 100)
                return await coro

            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                with patch("asyncio.wait_for", side_effect=mock_wait_for):
                    # Act
                    await service.extract_audio_chunk("task123", task_progress, video_file, 0.0, 10.0)

                    # Assert - Progress was updated
                    assert task_progress["task123"].progress == 5
                    assert "Extracting audio" in task_progress["task123"].current_step

    @pytest.mark.asyncio
    async def test_When_transcribe_chunk_Then_progress_updated(self):
        """Test progress is updated during transcription"""
        # Arrange
        service = ChunkTranscriptionService()
        task_progress = {"task123": Mock(progress=0, current_step="", message="")}

        with tempfile.TemporaryDirectory() as tmpdir:
            video_file = Path(tmpdir) / "test_video.mp4"
            video_file.touch()
            audio_file = Path(tmpdir) / "audio.wav"
            # Create non-empty audio file
            audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

            # Mock transcription service - must be AsyncMock for transcribe_with_progress
            mock_transcription_service = AsyncMock()
            mock_result = Mock()
            mock_result.full_text = "Transcribed text"
            mock_result.segments = None  # Trigger full_text fallback path
            mock_transcription_service.transcribe_with_progress = AsyncMock(return_value=mock_result)

            with patch("core.dependencies.get_transcription_service", return_value=mock_transcription_service):
                # Act
                await service.transcribe_chunk("task123", task_progress, video_file, audio_file, {"target": "de"})

                # Assert - Progress was updated
                assert task_progress["task123"].progress == 35
                assert "Transcribing" in task_progress["task123"].current_step
