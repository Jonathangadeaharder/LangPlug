"""
ChunkTranscriptionService - Handle audio extraction and transcription for video chunks
Extracted from chunk_processor.py for better separation of concerns
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
    Service responsible for audio extraction and transcription of video chunks
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

            # Execute ffmpeg command with timeout (10 minutes max)
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            try:
                _stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=600,  # 10 minutes timeout
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                raise ChunkTranscriptionError("FFmpeg audio extraction timed out after 600 seconds")

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace") if stderr else "Unknown ffmpeg error"
                # Clean up partial output file if it exists
                if audio_output.exists():
                    try:
                        audio_output.unlink()
                        logger.debug(f"Cleaned up partial audio file: {audio_output}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup partial file: {cleanup_error}")
                raise ChunkTranscriptionError(f"FFmpeg audio extraction failed: {error_msg}")

            if not audio_output.exists():
                raise ChunkTranscriptionError(f"Audio extraction failed: Output file not created at {audio_output}")

            logger.info(f"Audio extracted for {video_file.name} ({start_time}-{end_time}s) -> {audio_output}")
            return audio_output

        except FileNotFoundError:
            logger.error("FFmpeg not found - cannot extract audio chunk")
            raise ChunkTranscriptionError(
                "FFmpeg is not installed or not in PATH. "
                "Please install FFmpeg to enable video chunk processing. "
                "See: https://ffmpeg.org/download.html"
            )

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
            raise ChunkTranscriptionError(f"Audio extraction failed: {e}")

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
        from core.service_dependencies import get_transcription_service

        transcription_service = get_transcription_service()
        if not transcription_service:
            raise ChunkTranscriptionError("Transcription service is not available. Please check server configuration.")

        try:
            # Transcribe the audio chunk
            if audio_file != video_file:  # We have an actual audio file
                logger.info(f"Transcribing audio chunk: {audio_file}")
                # Use the transcription service to process the audio chunk
                # Run synchronous transcribe in executor to avoid blocking
                import asyncio

                transcription_result = await asyncio.to_thread(
                    transcription_service.transcribe, str(audio_file), language=target_language
                )

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
                logger.error(f"Audio file equals video file - no audio extraction occurred")
                raise ChunkTranscriptionError(
                    "Cannot transcribe chunk: Audio extraction did not produce a separate audio file. "
                    "This indicates FFmpeg is not available or failed."
                )

        except ChunkTranscriptionError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise ChunkTranscriptionError(f"Chunk transcription failed: {e}")

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
            raise ChunkTranscriptionError(f"SRT creation from segments failed: {e}")

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
            raise ChunkTranscriptionError(f"SRT creation failed: {e}")

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
