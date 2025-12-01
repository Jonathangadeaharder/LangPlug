"""
Audio extraction utilities for video files.

Provides centralized video-to-audio conversion using MoviePy
to eliminate code duplication across transcription services.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.config.logging_config import get_logger

logger = get_logger(__name__)


def extract_audio_from_video(
    video_path: str | Path,
    output_path: str | Path | None = None,
    sample_rate: int = 16000,
) -> str:
    """
    Extract audio track from video file.

    Args:
        video_path: Path to input video file
        output_path: Path for output audio file (auto-generated if None)
        sample_rate: Audio sample rate in Hz (16000 for most ML models)

    Returns:
        Path to extracted audio file

    Raises:
        ValueError: If video has no audio track
        ImportError: If moviepy is not installed
    """
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        # Fallback for older moviepy versions
        try:
            from moviepy import VideoFileClip
        except ImportError as e:
            raise ImportError(
                "moviepy is required for video audio extraction. Install with: pip install moviepy"
            ) from e

    # Generate output path if not provided
    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    else:
        output_path = str(output_path)

    video_path_str = str(video_path)
    logger.debug("Extracting audio", video=video_path_str)

    # Load video and extract audio
    video = VideoFileClip(video_path_str)
    audio = video.audio

    if audio is None:
        video.close()
        raise ValueError(f"No audio track found in {video_path_str}")

    # Write audio file with specified sample rate
    # logger=None suppresses moviepy's verbose output
    audio.write_audiofile(output_path, fps=sample_rate, logger=None)

    # Clean up resources
    video.close()

    logger.debug("Audio extracted", output=output_path)
    return output_path
