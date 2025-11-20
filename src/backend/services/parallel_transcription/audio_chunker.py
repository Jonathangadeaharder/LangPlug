"""
Audio Chunker with Intelligent Silence Detection

Splits audio files into processable chunks for parallel transcription.
Implements silence detection for natural chunk boundaries to prevent
word splitting at chunk edges.

Based on research from fast-audio-video-transcribe (mharrvic).
"""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioChunkingError(Exception):
    """Exception for audio chunking errors"""
    pass


class AudioChunker:
    """
    Split audio files into processable chunks for parallel transcription.

    Features:
    - Intelligent silence detection for chunk boundaries
    - Configurable chunk duration (default: 30s, Whisper's native chunk size)
    - Overlap between chunks to prevent word boundary issues
    - FFmpeg-based audio extraction and analysis

    Example:
        ```python
        chunker = AudioChunker(Path("/videos/video.mp4"))

        # Get duration
        duration = chunker.get_duration()

        # Create intelligent chunks
        chunks = chunker.create_intelligent_chunks()
        # Returns: [(0.0, 28.5), (26.5, 58.3), ...]

        # Extract a chunk
        chunk_file = await chunker.extract_chunk(0.0, 30.0, 0)

        # Cleanup
        chunker.cleanup()
        ```
    """

    CHUNK_DURATION = 30  # seconds (Whisper's native chunk size)
    OVERLAP = 2  # seconds of overlap to prevent word boundary issues
    SILENCE_THRESHOLD = -30  # dB (silence detection threshold)
    MIN_SILENCE_DURATION = 0.5  # seconds (minimum silence duration)

    def __init__(self, audio_path: Path):
        """
        Initialize audio chunker.

        Args:
            audio_path: Path to audio or video file
        """
        self.audio_path = audio_path
        self.temp_dir = Path(tempfile.mkdtemp(prefix="langplug_chunks_"))
        logger.info(f"AudioChunker initialized for {audio_path}")
        logger.info(f"Temp directory: {self.temp_dir}")

    def get_duration(self) -> float:
        """
        Extract audio duration using ffprobe.

        Returns:
            Duration in seconds

        Raises:
            AudioChunkingError: If ffprobe fails
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(self.audio_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            duration = float(result.stdout.strip())
            logger.info(f"Audio duration: {duration:.2f}s")
            return duration

        except FileNotFoundError as e:
            raise AudioChunkingError(
                "ffprobe not found. Please install FFmpeg: https://ffmpeg.org/download.html"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise AudioChunkingError(f"ffprobe timed out for {self.audio_path}") from e
        except (subprocess.CalledProcessError, ValueError) as e:
            raise AudioChunkingError(f"Failed to get duration: {e}") from e

    def detect_silence_points(
        self,
        min_silence_duration: float = None,
        silence_threshold: int = None
    ) -> list[float]:
        """
        Detect silence points for intelligent chunking.

        Uses FFmpeg's silencedetect filter to find natural pauses in audio.
        These points become preferred chunk boundaries.

        Args:
            min_silence_duration: Minimum silence duration in seconds (default: 0.5)
            silence_threshold: Silence threshold in dB (default: -30)

        Returns:
            List of timestamps where silence occurs

        Example:
            >>> chunker.detect_silence_points()
            [15.3, 28.7, 45.2, 62.1, ...]  # Timestamps of silence
        """
        min_duration = min_silence_duration or self.MIN_SILENCE_DURATION
        threshold = silence_threshold or self.SILENCE_THRESHOLD

        try:
            cmd = [
                "ffmpeg",
                "-i", str(self.audio_path),
                "-af", f"silencedetect=noise={threshold}dB:d={min_duration}",
                "-f", "null",
                "-"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False  # silencedetect writes to stderr, not an error
            )

            # Parse silence timestamps from ffmpeg output
            silence_points = []
            for line in result.stderr.split('\n'):
                if "silence_end:" in line:
                    # Extract timestamp from line like:
                    # [silencedetect @ 0x...] silence_end: 28.745 | silence_duration: 0.523
                    try:
                        timestamp_str = line.split("silence_end:")[1].split("|")[0].strip()
                        timestamp = float(timestamp_str)
                        silence_points.append(timestamp)
                    except (IndexError, ValueError):
                        continue

            logger.info(f"Detected {len(silence_points)} silence points")
            return silence_points

        except FileNotFoundError as e:
            logger.warning("ffmpeg not found for silence detection, using uniform chunks")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("Silence detection timed out, using uniform chunks")
            return []
        except Exception as e:
            logger.warning(f"Silence detection failed: {e}, using uniform chunks")
            return []

    def create_intelligent_chunks(self) -> list[tuple[float, float]]:
        """
        Create chunks aligned with silence points for better transcription quality.

        Algorithm:
        1. Get total duration
        2. Detect silence points
        3. Create chunks of ~30s duration
        4. Prefer chunk boundaries at silence points (±5s tolerance)
        5. Add 2s overlap between chunks

        Returns:
            List of (start_time, end_time) tuples

        Example:
            >>> chunker.create_intelligent_chunks()
            [
                (0.0, 28.5),      # Chunk 0: ends at silence point
                (26.5, 58.3),     # Chunk 1: 2s overlap, ends at silence
                (56.3, 85.0),     # Chunk 2: continues to end
            ]
        """
        duration = self.get_duration()
        silence_points = self.detect_silence_points()

        chunks = []
        current_start = 0.0

        while current_start < duration:
            target_end = min(current_start + self.CHUNK_DURATION, duration)

            # Find nearest silence point within ±5 seconds of target
            if silence_points:
                nearby_silences = [
                    s for s in silence_points
                    if target_end - 5 < s < target_end + 5 and s > current_start
                ]

                if nearby_silences:
                    # Use the silence point closest to target end
                    chunk_end = min(nearby_silences, key=lambda s: abs(s - target_end))
                else:
                    chunk_end = target_end
            else:
                chunk_end = target_end

            # Ensure we don't exceed duration
            chunk_end = min(chunk_end, duration)

            chunks.append((current_start, chunk_end))

            # Next chunk starts with overlap
            current_start = chunk_end - self.OVERLAP
            if current_start >= duration:
                break

        logger.info(f"Created {len(chunks)} intelligent chunks for {duration:.1f}s audio")
        for i, (start, end) in enumerate(chunks):
            logger.debug(f"  Chunk {i}: {start:.1f}s - {end:.1f}s ({end-start:.1f}s)")

        return chunks

    async def extract_chunk(
        self,
        start: float,
        end: float,
        chunk_index: int
    ) -> Path:
        """
        Extract a single audio chunk using ffmpeg.

        Creates a 16kHz mono WAV file optimized for Whisper transcription.

        Args:
            start: Start time in seconds
            end: End time in seconds
            chunk_index: Chunk number (for filename)

        Returns:
            Path to extracted chunk file

        Raises:
            AudioChunkingError: If extraction fails
        """
        output_path = self.temp_dir / f"chunk_{chunk_index:04d}.wav"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(self.audio_path),
            "-ss", str(start),
            "-to", str(end),
            "-ar", "16000",      # Whisper requires 16kHz
            "-ac", "1",          # Mono
            "-c:a", "pcm_s16le", # PCM 16-bit
            str(output_path)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            _stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                raise AudioChunkingError(f"FFmpeg extraction failed: {error_msg}")

            if not output_path.exists():
                raise AudioChunkingError(f"Chunk file not created: {output_path}")

            logger.debug(f"Extracted chunk {chunk_index}: {start:.1f}s - {end:.1f}s")
            return output_path

        except TimeoutError as e:
            raise AudioChunkingError(f"Chunk extraction timed out: chunk {chunk_index}") from e
        except FileNotFoundError as e:
            raise AudioChunkingError(
                "ffmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
            ) from e
        except Exception as e:
            raise AudioChunkingError(f"Chunk extraction failed: {e}") from e

    def cleanup(self):
        """Remove temporary chunk files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
