"""
Chunk Transcription Service

Audio extraction and speech-to-text transcription for video chunks.
This module handles FFmpeg-based audio extraction and Whisper-based transcription with SRT generation.

Key Components:
    - ChunkTranscriptionService: Main service for audio extraction and transcription
    - FFmpeg integration for audio extraction
    - Whisper model integration for transcription
    - SRT file generation from transcription segments

Processing Steps:
    1. Extract audio chunk using FFmpeg (PCM 16kHz mono)
    2. Transcribe using Whisper model (language-specific)
    3. Convert segments to SRT format
    4. Cleanup temporary audio files

Usage Example:
    ```python
    service = ChunkTranscriptionService()

    # Extract audio chunk
    audio_file = await service.extract_audio_chunk(
        task_id="task_123",
        task_progress=progress_dict,
        video_file=Path("/videos/video.mp4"),
        start_time=0.0,
        end_time=30.0
    )

    # Transcribe chunk
    srt_file = await service.transcribe_chunk(
        task_id="task_123",
        task_progress=progress_dict,
        video_file=Path("/videos/video.mp4"),
        audio_file=audio_file,
        language_preferences={"target": "de"},
        start_time=0.0,
        end_time=30.0
    )

    # Cleanup
    service.cleanup_temp_audio_file(audio_file, video_file)
    ```

Dependencies:
    - FFmpeg: External tool for audio extraction (required, must be in PATH)
    - Whisper: Speech recognition model via transcription service
    - asyncio: Subprocess management for FFmpeg
    - utils.srt_parser: SRT file formatting

Thread Safety:
    Yes. Service is stateless, all operations use local variables.

Performance Notes:
    - Audio extraction: ~2-5 seconds per 30s chunk (I/O bound)
    - Transcription: ~5-10 seconds per 30s chunk (GPU accelerated if available)
    - FFmpeg timeout: 600 seconds (10 minutes)
    - Audio format: PCM 16-bit 16kHz mono (optimized for speech recognition)

Error Handling:
    - Raises ChunkTranscriptionError on failures
    - Automatically cleans up partial files on error
    - Handles FFmpeg not found, timeout, and process errors
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

# Lazy import to avoid circular dependencies
from core.config import settings
from services.interfaces.transcription_interface import IChunkTranscriptionService

logger = logging.getLogger(__name__)


class ChunkTranscriptionError(Exception):
    """Exception for chunk transcription errors"""

    pass


class ChunkTranscriptionService(IChunkTranscriptionService):
    """
    Service for extracting audio and transcribing video chunks to text.

    Handles the complete audio-to-text pipeline: FFmpeg audio extraction, Whisper transcription,
    and SRT file generation with proper timestamp formatting.

    Example:
        ```python
        service = ChunkTranscriptionService()

        # Extract audio (creates .wav file)
        audio = await service.extract_audio_chunk(
            "task_1", progress, Path("video.mp4"), 0.0, 30.0
        )
        # Creates: video_chunk_0s_30s.wav

        # Transcribe (creates .srt file)
        srt = await service.transcribe_chunk(
            "task_1", progress, Path("video.mp4"), audio,
            {"target": "de"}, 0.0, 30.0
        )
        # Creates: video.srt with German transcription

        # Cleanup temp audio
        service.cleanup_temp_audio_file(audio, Path("video.mp4"))
        ```

    Note:
        Implements IChunkTranscriptionService interface.
        Audio extraction requires FFmpeg in system PATH.
        Transcription requires Whisper model loaded in transcription service.
        Automatically handles temporary file cleanup on success and error.
    """

    async def extract_audio_chunk(
        self, task_id: str, task_progress: dict[str, Any], video_file: Path, start_time: float, end_time: float
    ) -> Path:
        """Extract audio chunk from video using ffmpeg"""
        task_progress[task_id].progress = 5
        task_progress[task_id].current_step = "Extracting audio chunk..."
        task_progress[task_id].message = "Isolating audio for this segment"

        # Create output audio file path
        duration = end_time - start_time
        audio_output = video_file.parent / f"{video_file.stem}_chunk_{start_time}s_{end_time}s.wav"

        logger.info(f"Extracting audio from video: {video_file}")
        logger.info(f"Output audio file: {audio_output}")

        try:
            # Build ffmpeg command for audio extraction
            cmd = [
                "ffmpeg",
                "-i",
                str(video_file),
                "-ss",
                str(start_time),
                "-t",
                str(duration),
                "-vn",  # No video
                "-acodec",
                "pcm_s16le",  # PCM 16-bit little-endian
                "-ar",
                "16000",  # 16kHz sample rate for speech recognition
                "-ac",
                "1",  # Mono channel
                "-y",  # Overwrite output file
                str(audio_output),
            ]

            # On Windows, check if we can use async subprocess or need workaround
            import sys

            process = None
            if sys.platform == "win32":
                loop = asyncio.get_running_loop()
                if not isinstance(loop, asyncio.ProactorEventLoop):
                    # SelectorEventLoop doesn't support subprocesses - use sync fallback
                    logger.info("[WINDOWS FIX] Using sync subprocess fallback (SelectorEventLoop detected)")
                    import concurrent.futures
                    import subprocess

                    def run_ffmpeg_sync():
                        result = subprocess.run(cmd, check=False, capture_output=True, timeout=600)
                        return result.returncode, result.stdout, result.stderr

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        returncode, _stdout, stderr = await loop.run_in_executor(pool, run_ffmpeg_sync)

                    # Create a fake process object for compatibility
                    class FakeProcess:
                        def __init__(self, rc):
                            self.returncode = rc

                    process = FakeProcess(returncode)
                else:
                    # ProactorEventLoop supports async subprocesses
                    process = await asyncio.create_subprocess_exec(
                        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    _stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            else:
                # Unix systems support async subprocesses normally
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                _stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace") if stderr else "Unknown ffmpeg error"
                logger.error(f"FFmpeg failed for video: {video_file}")
                logger.error(f"FFmpeg error output: {error_msg}")
                # Clean up partial output file if it exists
                if audio_output.exists():
                    try:
                        audio_output.unlink()
                        logger.debug(f"Cleaned up partial audio file: {audio_output}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup partial file: {cleanup_error}")
                raise ChunkTranscriptionError(
                    f"FFmpeg audio extraction failed for {video_file.name}. "
                    f"Video path: {video_file}. Error: {error_msg}"
                )

            if not audio_output.exists():
                logger.error("FFmpeg completed but output file not created")
                logger.error(f"Expected output: {audio_output}")
                logger.error(f"Input video: {video_file}")
                logger.error(f"Video exists: {video_file.exists()}")
                raise ChunkTranscriptionError(
                    f"Audio extraction failed: FFmpeg completed but output file not created. "
                    f"Video: {video_file}, Expected output: {audio_output}"
                )

            # Check if audio file is empty (0 bytes) - this causes Whisper to crash
            audio_size = audio_output.stat().st_size
            if audio_size == 0:
                logger.error(f"FFmpeg created empty audio file: {audio_output}")
                audio_output.unlink()  # Clean up empty file
                raise ChunkTranscriptionError(
                    f"Audio extraction failed: FFmpeg created empty audio file (0 bytes). "
                    f"The video segment {start_time}-{end_time}s may not contain audio. "
                    f"Video: {video_file.name}"
                )
            
            # Also check for suspiciously small files (< 1KB for any chunk > 1s)
            min_expected_size = int(duration * 16000 * 2 * 0.01)  # ~1% of expected PCM size
            if audio_size < min_expected_size and duration > 1:
                logger.warning(
                    f"Audio file suspiciously small: {audio_size} bytes for {duration}s chunk "
                    f"(expected at least {min_expected_size} bytes). File: {audio_output}"
                )

            logger.info(f"Audio extracted for {video_file.name} ({start_time}-{end_time}s) -> {audio_output} ({audio_size} bytes)")
            return audio_output

        except FileNotFoundError as e:
            logger.error("FFmpeg not found - cannot extract audio chunk")
            raise ChunkTranscriptionError(
                "FFmpeg is not installed or not in PATH. "
                "Please install FFmpeg to enable video chunk processing. "
                "See: https://ffmpeg.org/download.html"
            ) from e

        except TimeoutError as e:
            logger.error(f"FFmpeg process timed out for video: {video_file}")
            # Kill the process if it exists and has a kill method
            if process is not None and hasattr(process, "kill"):
                try:
                    process.kill()
                    if hasattr(process, "wait"):
                        await process.wait()
                    logger.debug("Killed timed-out FFmpeg process")
                except Exception as kill_error:
                    logger.warning(f"Failed to kill timed-out process: {kill_error}")
            # Clean up partial output file
            if audio_output.exists():
                try:
                    audio_output.unlink()
                    logger.debug(f"Cleaned up partial audio file after timeout: {audio_output}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup after timeout: {cleanup_error}")
            raise ChunkTranscriptionError(f"Audio extraction timed out for {video_file.name}") from e

        except ChunkTranscriptionError:
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            # Cleanup partial file on unexpected error
            if audio_output.exists():
                try:
                    audio_output.unlink()
                    logger.debug(f"Cleaned up audio file after error: {audio_output}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup after error: {cleanup_error}")
            logger.error(f"Audio extraction error: {e}", exc_info=True)
            raise ChunkTranscriptionError(f"Audio extraction failed: {e}") from e

    async def _simulate_transcription_progress(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        audio_duration_seconds: float,
        stop_event: asyncio.Event,
    ) -> None:
        """
        Simulate progress updates during transcription.
        
        Whisper doesn't provide progress callbacks, so we estimate progress based on
        audio duration. Typical transcription speed is ~10-30x realtime for whisper-tiny,
        ~2-5x for larger models.
        """
        # Estimate transcription time: assume ~5x realtime for whisper-tiny (conservative)
        # A 20-min (1200s) chunk might take ~240s = 4 min to transcribe
        estimated_time_seconds = audio_duration_seconds / 5.0
        
        # Progress goes from 5% to 35% during transcription (30% range)
        start_progress = 5
        end_progress = 35
        progress_range = end_progress - start_progress
        
        # Update every 2 seconds
        update_interval = 2.0
        elapsed = 0.0
        
        while not stop_event.is_set():
            await asyncio.sleep(update_interval)
            elapsed += update_interval
            
            # Calculate progress based on elapsed time vs estimated time
            # Cap at 95% of target to leave room for actual completion
            progress_fraction = min(elapsed / estimated_time_seconds, 0.95)
            new_progress = start_progress + (progress_range * progress_fraction)
            
            task_progress[task_id].progress = new_progress
            
            # Update message with elapsed time
            elapsed_min = int(elapsed // 60)
            elapsed_sec = int(elapsed % 60)
            if elapsed_min > 0:
                task_progress[task_id].message = f"Transcribing... ({elapsed_min}m {elapsed_sec}s elapsed)"
            else:
                task_progress[task_id].message = f"Transcribing... ({elapsed_sec}s elapsed)"

    async def transcribe_chunk(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        audio_file: Path,
        language_preferences: dict[str, Any] | None = None,
        start_time: float = 0,
        end_time: float = 30,
    ) -> str:
        """Transcribe the audio chunk to text"""
        task_progress[task_id].progress = 5
        target_language = language_preferences.get("target") if language_preferences else settings.default_language
        task_progress[task_id].current_step = "Transcribing audio..."
        task_progress[task_id].message = f"Converting speech ({target_language}) to text"

        # Lazy import to avoid circular dependencies
        from core.dependencies import get_transcription_service

        transcription_service = get_transcription_service()
        if not transcription_service:
            raise ChunkTranscriptionError("Transcription service is not available. Please check server configuration.")

        try:
            # Transcribe the audio chunk
            if audio_file != video_file:  # We have an actual audio file
                logger.info(f"Transcribing audio chunk: {audio_file}")
                
                # Calculate audio duration for progress estimation
                audio_duration = end_time - start_time
                
                # Start progress simulation in background
                stop_progress = asyncio.Event()
                progress_task = asyncio.create_task(
                    self._simulate_transcription_progress(
                        task_id, task_progress, audio_duration, stop_progress
                    )
                )
                
                try:
                    # Run synchronous transcribe in executor to avoid blocking
                    transcription_result = await asyncio.to_thread(
                        transcription_service.transcribe, str(audio_file), language=target_language
                    )
                finally:
                    # Stop progress simulation
                    stop_progress.set()
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass

                # Extract transcribed segments from result
                srt_output = video_file.with_suffix(".srt")

                if hasattr(transcription_result, "segments") and transcription_result.segments:
                    # Create SRT from Whisper segments with proper timestamps
                    self._create_srt_from_segments(transcription_result.segments, srt_output)
                    logger.info(
                        f"Created SRT with {len(transcription_result.segments)} segments "
                        f"from {len(transcription_result.full_text)} chars"
                    )
                elif hasattr(transcription_result, "full_text"):
                    # Fallback: single segment SRT
                    transcribed_text = transcription_result.full_text
                    self._create_chunk_srt(transcribed_text, srt_output, 0, 30)
                    logger.info(f"Created single-segment SRT from {len(transcribed_text)} chars")
                else:
                    raise ChunkTranscriptionError("Transcription result has no usable text or segments")

                # Update progress to end of transcription phase
                task_progress[task_id].progress = 35
                task_progress[task_id].message = "Transcription complete"

                logger.info(f"Transcription completed for {video_file.name} -> {srt_output}")
                return str(srt_output)

            else:
                # No real audio file extracted - transcription service unavailable
                logger.error("Audio file equals video file - no audio extraction occurred")
                raise ChunkTranscriptionError(
                    "Cannot transcribe chunk: Audio extraction did not produce a separate audio file. "
                    "This indicates FFmpeg is not available or failed."
                )

        except ChunkTranscriptionError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise ChunkTranscriptionError(f"Chunk transcription failed: {e}") from e

    def _create_srt_from_segments(self, segments: list, output_path: Path) -> None:
        """
        Create SRT file from transcription segments

        Args:
            segments: List of TranscriptionSegment objects from Whisper
            output_path: Path to output SRT file
        """
        try:
            from utils.srt_parser import SRTParser, SRTSegment

            # Convert TranscriptionSegments to SRTSegments
            srt_segments = []
            for i, seg in enumerate(segments, start=1):
                srt_segment = SRTSegment(
                    index=i, start_time=seg.start_time, end_time=seg.end_time, text=seg.text.strip()
                )
                srt_segments.append(srt_segment)

            # Use SRTParser to write properly formatted SRT
            parser = SRTParser()
            srt_content = parser.segments_to_srt(srt_segments)

            # Write to file
            output_path.write_text(srt_content, encoding="utf-8")

            logger.info(f"Created SRT file with {len(srt_segments)} segments: {output_path}")

        except Exception as e:
            logger.error(f"Failed to create SRT from segments: {e}")
            raise ChunkTranscriptionError(f"SRT creation from segments failed: {e}") from e

    def _create_chunk_srt(self, text: str, output_path: Path, start_time: float, duration: float) -> None:
        """Create an SRT file from transcribed text"""
        try:
            # Simple SRT format for the chunk
            end_time = start_time + duration

            # Format timestamps
            start_ts = self._format_srt_timestamp(start_time)
            end_ts = self._format_srt_timestamp(end_time)

            # Create SRT content
            srt_content = f"1\n{start_ts} --> {end_ts}\n{text.strip()}\n\n"

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

            logger.info(f"Created SRT file: {output_path}")

        except Exception as e:
            logger.error(f"Failed to create SRT file: {e}")
            raise ChunkTranscriptionError(f"SRT creation failed: {e}") from e

    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def find_matching_srt_file(self, video_file: Path) -> str:
        """
        Find existing SRT file for video or return where it should be created

        Args:
            video_file: Path to the video file

        Returns:
            Path to existing or target SRT file
        """
        # Try different SRT naming conventions
        srt_candidates = [
            video_file.with_suffix(".srt"),
            video_file.with_suffix(".de.srt"),
            video_file.with_suffix(".en.srt"),
            video_file.with_name(f"{video_file.stem}_subtitles.srt"),
        ]

        for srt_path in srt_candidates:
            if srt_path.exists():
                logger.info(f"Found existing SRT file: {srt_path}")
                return str(srt_path)

        # Default to simple .srt extension
        default_srt = video_file.with_suffix(".srt")
        logger.info(f"No existing SRT found, will use: {default_srt}")
        return str(default_srt)

    def cleanup_temp_audio_file(self, audio_file: Path, video_file: Path) -> None:
        """
        Clean up temporary audio file after transcription

        Args:
            audio_file: Path to temporary audio file
            video_file: Original video file (won't be deleted)
        """
        # Only delete if it's a generated audio file (not the original video)
        if audio_file != video_file and audio_file.exists():
            try:
                audio_file.unlink()
                logger.info(f"Cleaned up temporary audio file: {audio_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary audio file {audio_file}: {e}")
