"""
OpenAI Whisper Transcription Service Implementation
State-of-the-art speech recognition
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import whisper

from .interface import ITranscriptionService, TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


class WhisperTranscriptionService(ITranscriptionService):
    """
    OpenAI Whisper implementation of transcription service
    Supports multiple languages and model sizes
    """

    # Available Whisper models
    AVAILABLE_MODELS = [
        "tiny",  # 39M parameters
        "base",  # 74M parameters
        "small",  # 244M parameters
        "medium",  # 769M parameters
        "large",  # 1550M parameters
        "large-v2",  # 1550M parameters (improved)
        "large-v3",  # 1550M parameters (latest)
        "large-v3-turbo",  # Faster large model
    ]

    def __init__(self, model_size: str = "large-v3-turbo", device: str | None = None, download_root: str | None = None):
        """
        Initialize Whisper transcription service

        Args:
            model_size: Size of Whisper model to use
            device: Device to use ('cuda' or 'cpu')
            download_root: Directory to download model to
        """
        if model_size not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model size: {model_size}. Choose from: {', '.join(self.AVAILABLE_MODELS)}")

        self.model_size = model_size
        self.device = device
        self.download_root = download_root
        self._model = None

    def initialize(self) -> None:
        """Initialize the Whisper model"""
        if self._model is None:
            import os

            # Check if model is already downloaded
            model_cache_dir = self.download_root or os.path.expanduser("~/.cache/whisper")
            model_files = {
                "tiny": "tiny.pt",
                "base": "base.pt",
                "small": "small.pt",
                "medium": "medium.pt",
                "large": "large.pt",
                "large-v2": "large-v2.pt",
                "large-v3": "large-v3.pt",
                "large-v3-turbo": "large-v3-turbo.pt",
            }

            model_file = model_files.get(self.model_size, f"{self.model_size}.pt")
            model_path = Path(model_cache_dir) / model_file

            if not model_path.exists():
                model_size_mb = {
                    "tiny": 39,
                    "base": 74,
                    "small": 244,
                    "medium": 769,
                    "large": 1550,
                    "large-v2": 1550,
                    "large-v3": 1550,
                    "large-v3-turbo": 809,
                }.get(self.model_size, 1000)

                logger.info(f"[MODEL DOWNLOAD] Downloading Whisper model '{self.model_size}' (~{model_size_mb}MB)")
                logger.info("[MODEL DOWNLOAD] First-time download in progress...")
                logger.info(f"[MODEL DOWNLOAD] Model will be cached at: {model_path}")
                logger.info("[MODEL DOWNLOAD] Please wait, this is a one-time download...")
            else:
                logger.info(f"[MODEL LOAD] Loading cached Whisper model: {self.model_size}")
                logger.info(f"[MODEL LOAD] Model location: {model_path}")

            logger.info(f"[MODEL INIT] Initializing Whisper {self.model_size}...")
            self._model = whisper.load_model(self.model_size, device=self.device, download_root=self.download_root)
            logger.info(f"[MODEL READY] Whisper model '{self.model_size}' loaded successfully!")
            logger.info("[MODEL READY] Transcription service is now operational")

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Transcribe an audio file"""
        if not self.is_initialized:
            self.initialize()

        # Handle video files
        if self._is_video_file(audio_path):
            audio_path = self.extract_audio_from_video(audio_path)
            cleanup = True
        else:
            cleanup = False

        try:
            # Perform transcription
            result = self._model.transcribe(audio_path, language=language, task="transcribe")

            # Extract segments
            segments = []
            for seg in result.get("segments", []):
                segments.append(
                    TranscriptionSegment(
                        start_time=seg["start"],
                        end_time=seg["end"],
                        text=seg["text"].strip(),
                        metadata={"id": seg.get("id"), "tokens": seg.get("tokens", [])},
                    )
                )

            return TranscriptionResult(
                full_text=result["text"].strip(),
                segments=segments,
                language=result.get("language"),
                duration=segments[-1].end_time if segments else 0,
                metadata={"model": self.model_size, "task": "transcribe"},
            )
        finally:
            if cleanup and os.path.exists(audio_path):
                os.unlink(audio_path)

    def transcribe_with_timestamps(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Transcribe with detailed timestamps"""
        # Whisper always provides timestamps, so this is the same as transcribe
        return self.transcribe(audio_path, language)

    def transcribe_batch(self, audio_paths: list[str], language: str | None = None) -> list[TranscriptionResult]:
        """Transcribe multiple audio files in batch"""
        results = []
        for audio_path in audio_paths:
            result = self.transcribe(audio_path, language)
            results.append(result)
        return results

    def supports_video(self) -> bool:
        """Whisper supports video through audio extraction"""
        return True

    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> str:
        """Extract audio from video file"""
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            # Fallback for older moviepy versions
            from moviepy import VideoFileClip

        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

        video = VideoFileClip(video_path)
        audio = video.audio

        if audio is None:
            raise ValueError(f"No audio track found in {video_path}")

        audio.write_audiofile(output_path, logger=None)
        video.close()

        return output_path

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes"""
        # Whisper supports 99 languages
        return [
            "en",
            "zh",
            "de",
            "es",
            "ru",
            "ko",
            "fr",
            "ja",
            "pt",
            "tr",
            "pl",
            "ca",
            "nl",
            "ar",
            "sv",
            "it",
            "id",
            "hi",
            "fi",
            "vi",
            "he",
            "uk",
            "el",
            "ms",
            "cs",
            "ro",
            "da",
            "hu",
            "ta",
            "no",
            "th",
            "ur",
            "hr",
            "bg",
            "lt",
            "la",
            "mi",
            "ml",
            "cy",
            "sk",
            "te",
            "fa",
            "lv",
            "bn",
            "sr",
            "az",
            "sl",
            "kn",
            "et",
            "mk",
            "br",
            "eu",
            "is",
            "hy",
            "ne",
            "mn",
            "bs",
            "kk",
            "sq",
            "sw",
            "gl",
            "mr",
            "pa",
            "si",
            "km",
            "sn",
            "yo",
            "so",
            "af",
            "oc",
            "ka",
            "be",
            "tg",
            "sd",
            "gu",
            "am",
            "yi",
            "lo",
            "uz",
            "fo",
            "ht",
            "ps",
            "tk",
            "nn",
            "mt",
            "sa",
            "lb",
            "my",
            "bo",
            "tl",
            "mg",
            "as",
            "tt",
            "haw",
            "ln",
            "ha",
            "ba",
            "jw",
            "su",
        ]

    def cleanup(self) -> None:
        """Clean up resources and unload model"""
        if self._model is not None:
            del self._model
            self._model = None

    @property
    def service_name(self) -> str:
        """Get the name of this transcription service"""
        return f"Whisper-{self.model_size}"

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized"""
        return self._model is not None

    @property
    def model_info(self) -> dict[str, Any]:
        """Get information about the loaded model"""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        return {
            "name": "OpenAI Whisper",
            "size": self.model_size,
            "parameters": self._get_model_parameters(),
            "multilingual": self.model_size not in ["tiny.en", "base.en", "small.en", "medium.en"],
            "languages": len(self.get_supported_languages()),
        }

    def _is_video_file(self, file_path: str) -> bool:
        """Check if file is a video"""
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
        return Path(file_path).suffix.lower() in video_extensions

    def _get_model_parameters(self) -> str:
        """Get number of parameters for model size"""
        params = {
            "tiny": "39M",
            "base": "74M",
            "small": "244M",
            "medium": "769M",
            "large": "1550M",
            "large-v2": "1550M",
            "large-v3": "1550M",
            "large-v3-turbo": "809M",  # Turbo is smaller but faster
        }
        return params.get(self.model_size, "unknown")
