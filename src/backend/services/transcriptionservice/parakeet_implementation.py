"""
NVIDIA Parakeet Transcription Service Implementation
High-performance ASR using NVIDIA NeMo
"""

import os
from pathlib import Path
from typing import Any

from core.config.logging_config import get_logger

from .interface import ITranscriptionService, TranscriptionResult, TranscriptionSegment

logger = get_logger(__name__)


class ParakeetTranscriptionService(ITranscriptionService):
    """
    NVIDIA Parakeet implementation of transcription service
    Fast and accurate transcription using NeMo models
    """

    # Available Parakeet models
    AVAILABLE_MODELS = {
        "parakeet-tdt-1.1b": "nvidia/parakeet-tdt-1.1b",
        "parakeet-ctc-1.1b": "nvidia/parakeet-ctc-1.1b",
        "parakeet-ctc-0.6b": "nvidia/parakeet-ctc-0.6b",
        "parakeet-tdt-0.6b": "nvidia/parakeet-tdt-0.6b-v3",  # Updated to v3 model
    }

    def __init__(self, model_name: str = "parakeet-tdt-1.1b", device: str | None = None):
        """
        Initialize Parakeet transcription service

        Args:
            model_name: Name of Parakeet model to use
            device: Device to use ('cuda' or 'cpu')
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model: {model_name}. Choose from: {', '.join(self.AVAILABLE_MODELS.keys())}")

        self.model_name = model_name
        self.model_path = self.AVAILABLE_MODELS[model_name]
        self.device = device or "cuda" if self._cuda_available() else "cpu"
        self._model = None

    def initialize(self) -> None:
        """Initialize the Parakeet model"""
        if self._model is None:
            from core.gpu_utils import check_cuda_availability

            # Check CUDA availability
            cuda_available = check_cuda_availability("Parakeet")

            if not cuda_available:
                self.device = "cpu"

            try:
                import nemo.collections.asr as nemo_asr

                if cuda_available:
                    import torch

                    logger.info("GPU available for Parakeet", device=torch.cuda.get_device_name(0))
                    self.device = "cuda"

                logger.info("Loading Parakeet model", model=self.model_name)
                self._model = nemo_asr.models.ASRModel.from_pretrained(model_name=self.model_path)

                # Move model to device
                if self.device == "cuda" and self._cuda_available():
                    self._model = self._model.cuda()

                self._model.eval()
                logger.info("Parakeet model loaded", model=self.model_name)

            except ImportError as e:
                raise ImportError("NeMo toolkit not installed. Install with: pip install nemo_toolkit[asr]") from e

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
            transcriptions = self._model.transcribe([audio_path])

            # Handle different return formats
            if isinstance(transcriptions, list) and len(transcriptions) > 0:
                if isinstance(transcriptions[0], str):
                    # Simple text output
                    full_text = transcriptions[0]
                    segments = [TranscriptionSegment(start_time=0, end_time=0, text=full_text)]
                else:
                    # Output with timestamps
                    full_text = transcriptions[0].text if hasattr(transcriptions[0], "text") else str(transcriptions[0])

                    # Try to extract segments with timestamps
                    segments = self._extract_segments(transcriptions[0])
            else:
                raise ValueError("Unexpected transcription format")

            return TranscriptionResult(
                full_text=full_text,
                segments=segments,
                language="en",  # Parakeet is primarily English
                duration=self._get_audio_duration(audio_path),
                metadata={"model": self.model_name, "device": self.device},
            )
        finally:
            if cleanup and os.path.exists(audio_path):
                os.unlink(audio_path)

    def transcribe_with_timestamps(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Transcribe with detailed timestamps"""
        # Parakeet provides timestamps when available
        return self.transcribe(audio_path, language)

    def transcribe_batch(self, audio_paths: list[str], language: str | None = None) -> list[TranscriptionResult]:
        """Transcribe multiple audio files in batch"""
        if not self.is_initialized:
            self.initialize()

        # Parakeet supports batch processing
        transcriptions = self._model.transcribe(audio_paths)

        results = []
        for audio_path, transcription in zip(audio_paths, transcriptions, strict=False):
            if isinstance(transcription, str):
                full_text = transcription
                segments = [TranscriptionSegment(start_time=0, end_time=0, text=full_text)]
            else:
                full_text = transcription.text if hasattr(transcription, "text") else str(transcription)
                segments = self._extract_segments(transcription)

            results.append(
                TranscriptionResult(
                    full_text=full_text,
                    segments=segments,
                    language="en",
                    duration=self._get_audio_duration(audio_path),
                    metadata={"model": self.model_name, "device": self.device},
                )
            )

        return results

    def supports_video(self) -> bool:
        """Parakeet supports video through audio extraction"""
        return True

    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> str:
        """Extract audio from video file"""
        from services.media import extract_audio_from_video

        return extract_audio_from_video(video_path, output_path, sample_rate=16000)

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes"""
        # Parakeet is primarily English
        return ["en"]

    def cleanup(self) -> None:
        """Clean up resources and unload model"""
        if self._model is not None:
            del self._model
            self._model = None

            # Clear GPU cache if using CUDA
            if self.device == "cuda" and self._cuda_available():
                import torch

                torch.cuda.empty_cache()

    @property
    def service_name(self) -> str:
        """Get the name of this transcription service"""
        return f"Parakeet-{self.model_name}"

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
            "name": "NVIDIA Parakeet",
            "model": self.model_name,
            "device": self.device,
            "framework": "NeMo",
            "languages": ["English"],
        }

    def _is_video_file(self, file_path: str) -> bool:
        """Check if file is a video"""
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
        return Path(file_path).suffix.lower() in video_extensions

    def _cuda_available(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file"""
        try:
            from moviepy.editor import AudioFileClip

            with AudioFileClip(audio_path) as audio:
                return audio.duration
        except (ImportError, OSError, Exception) as e:
            logger.warning("Could not get audio duration", error=str(e))
            return 0.0

    def _extract_segments(self, transcription) -> list[TranscriptionSegment]:
        """Extract segments from Parakeet transcription output"""
        segments = []

        # Try to extract word-level timestamps if available
        if hasattr(transcription, "timestamps") and hasattr(transcription, "words"):
            words = transcription.words if hasattr(transcription, "words") else transcription.text.split()
            timestamps = transcription.timestamps

            for word, (start, end) in zip(words, timestamps, strict=False):
                segments.append(TranscriptionSegment(start_time=start, end_time=end, text=word))
        elif hasattr(transcription, "segments"):
            # Segment-level output
            for seg in transcription.segments:
                segments.append(
                    TranscriptionSegment(
                        start_time=seg.get("start", 0), end_time=seg.get("end", 0), text=seg.get("text", "")
                    )
                )
        else:
            # Fallback to single segment
            text = transcription.text if hasattr(transcription, "text") else str(transcription)
            segments.append(TranscriptionSegment(start_time=0, end_time=0, text=text))

        return segments
