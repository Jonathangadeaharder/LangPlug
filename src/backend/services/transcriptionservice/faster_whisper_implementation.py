"""
Faster-Whisper Transcription Service Implementation
CTranslate2-based reimplementation that is up to 4x faster than OpenAI Whisper
with lower memory usage and INT8 quantization support.

See: https://github.com/SYSTRAN/faster-whisper
"""

from typing import Any

from core.config.logging_config import get_logger

from .interface import ITranscriptionService, ProgressCallback, TranscriptionResult, TranscriptionSegment

logger = get_logger(__name__)


class FasterWhisperTranscriptionService(ITranscriptionService):
    """
    Faster-Whisper implementation using CTranslate2.

    Benefits over standard Whisper:
    - Up to 4x faster transcription
    - Lower memory usage
    - INT8 quantization support (even faster, less memory)
    - Batched transcription support
    - VAD filtering built-in
    """

    # Available model sizes
    # Standard models are downloaded from HuggingFace automatically
    # For turbo, use the HuggingFace model ID: deepdml/faster-whisper-large-v3-turbo-ct2
    AVAILABLE_MODELS = [
        # Standard faster-whisper models (auto-downloaded)
        "tiny",
        "tiny.en",
        "base",
        "base.en",
        "small",
        "small.en",
        "medium",
        "medium.en",
        "large-v1",
        "large-v2",
        "large-v3",
        "distil-large-v2",
        "distil-large-v3",
        "distil-medium.en",
        "distil-small.en",
        # HuggingFace models (turbo not in default faster-whisper)
        "deepdml/faster-whisper-large-v3-turbo-ct2",
    ]

    # Compute type options
    COMPUTE_TYPES = [
        "float32",
        "float16",  # GPU only, fastest
        "int8",  # CPU/GPU, good balance
        "int8_float16",  # GPU only, best for large models
    ]

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
        device: str | None = None,
        compute_type: str | None = None,
        download_root: str | None = None,
        num_workers: int = 1,
        cpu_threads: int = 4,
    ):
        """
        Initialize Faster-Whisper transcription service.

        Args:
            model_size: Size of Whisper model to use
            device: Device to use ('cuda', 'cpu', or 'auto')
            compute_type: Quantization type ('float16', 'int8', etc.)
            download_root: Directory to download model to
            num_workers: Number of workers for parallel processing
            cpu_threads: Number of CPU threads to use
        """
        # Map turbo alias
        if model_size == "turbo":
            model_size = "large-v3-turbo"

        self.model_size = model_size
        self.device = device or "auto"
        self.download_root = download_root
        self.num_workers = num_workers
        self.cpu_threads = cpu_threads
        self._model = None
        self._batched_model = None

        # Auto-select compute type based on device
        if compute_type:
            self.compute_type = compute_type
        elif self.device == "cuda":
            self.compute_type = "float16"
        else:
            self.compute_type = "int8"  # Best for CPU

    def initialize(self) -> None:
        """Initialize the Faster-Whisper model"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise ImportError("faster-whisper is not installed. Install it with: pip install faster-whisper") from e

            from core.gpu_utils import check_cuda_availability

            # Check CUDA availability
            cuda_available = check_cuda_availability("Faster-Whisper")

            # Determine device
            if self.device == "auto":
                device = "cuda" if cuda_available else "cpu"
            else:
                device = self.device

            # Adjust compute type for CPU
            if device == "cpu" and self.compute_type in ("float16", "int8_float16"):
                logger.warning("Compute type not supported on CPU, using int8", requested=self.compute_type)
                self.compute_type = "int8"

            logger.info("Loading Whisper model", model=self.model_size, device=device, compute_type=self.compute_type)

            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=self.compute_type,
                    download_root=self.download_root,
                    num_workers=self.num_workers,
                    cpu_threads=self.cpu_threads,
                )
                logger.info("Whisper model loaded")
            except Exception as e:
                logger.error("Failed to load model", error=str(e))
                raise

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """
        Transcribe an audio file using Faster-Whisper (synchronous, no progress).

        Args:
            audio_path: Path to audio file
            language: Optional language hint (e.g., 'en', 'de')

        Returns:
            TranscriptionResult with transcription
        """
        self.initialize()

        logger.debug("Transcribing", audio_path=audio_path)

        # Transcribe with VAD filter for better results
        segments_generator, info = self._model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )

        # Collect segments (this triggers the actual transcription)
        segments = []
        full_text_parts = []

        for seg in segments_generator:
            segments.append(
                TranscriptionSegment(
                    start_time=seg.start,
                    end_time=seg.end,
                    text=seg.text.strip(),
                    confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else None,
                    metadata={
                        "id": seg.id if hasattr(seg, "id") else None,
                        "no_speech_prob": seg.no_speech_prob if hasattr(seg, "no_speech_prob") else None,
                    },
                )
            )
            full_text_parts.append(seg.text)

        full_text = "".join(full_text_parts).strip()

        logger.info("Transcription complete", segments=len(segments), chars=len(full_text), language=info.language)

        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=info.language,
            duration=info.duration if hasattr(info, "duration") else (segments[-1].end_time if segments else 0),
            metadata={
                "model": self.model_size,
                "compute_type": self.compute_type,
                "language_probability": info.language_probability,
            },
        )

    async def transcribe_with_progress(
        self,
        audio_path: str,
        language: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file with REAL progress tracking.

        Unlike the synchronous transcribe(), this method:
        - Reports actual progress based on transcribed audio duration
        - Yields to the event loop between segments for responsive updates
        - Provides detailed per-segment status messages

        Args:
            audio_path: Path to audio file
            language: Optional language hint (e.g., 'en', 'de')
            progress_callback: Async callback receiving (fraction: 0-1, message: str)

        Returns:
            TranscriptionResult with transcription
        """
        import asyncio

        self.initialize()

        logger.debug("Transcribing with progress", audio_path=audio_path)

        # Report starting
        if progress_callback:
            await progress_callback(0.0, "Initializing transcription...")

        # Transcribe with VAD filter for better results
        segments_generator, info = self._model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )

        # Get total duration for progress calculation
        total_duration = info.duration if hasattr(info, "duration") else 0
        if total_duration <= 0:
            # Fallback: estimate from file size (rough approximation)
            import os

            file_size = os.path.getsize(audio_path)
            # 16kHz mono 16-bit = 32000 bytes/second
            total_duration = file_size / 32000
            logger.warning("No duration in info, estimated", duration=total_duration)

        logger.debug("Total audio duration", duration=total_duration)

        # Collect segments with progress updates
        segments = []
        full_text_parts = []
        segment_count = 0

        for seg in segments_generator:
            segment_count += 1

            segments.append(
                TranscriptionSegment(
                    start_time=seg.start,
                    end_time=seg.end,
                    text=seg.text.strip(),
                    confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else None,
                    metadata={
                        "id": seg.id if hasattr(seg, "id") else None,
                        "no_speech_prob": seg.no_speech_prob if hasattr(seg, "no_speech_prob") else None,
                    },
                )
            )
            full_text_parts.append(seg.text)

            # Calculate REAL progress based on transcribed duration
            if total_duration > 0:
                fraction = min(seg.end / total_duration, 1.0)
            else:
                # Fallback: count-based (less accurate but better than nothing)
                fraction = min(segment_count / 100, 0.99)  # Assume ~100 segments max

            # Report progress
            if progress_callback:
                message = f"Transcribed {seg.end:.1f}s / {total_duration:.1f}s"
                await progress_callback(fraction, message)

            # Yield to event loop to allow other async operations
            # This is crucial for responsive WebSocket updates
            await asyncio.sleep(0)  # Zero-sleep yields to event loop

        full_text = "".join(full_text_parts).strip()

        # Report completion
        if progress_callback:
            await progress_callback(1.0, f"Transcription complete: {segment_count} segments")

        logger.info(
            f"[FASTER-WHISPER] Transcription complete: {len(segments)} segments, "
            f"{len(full_text)} chars, language: {info.language}"
        )

        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=info.language,
            duration=total_duration,
            metadata={
                "model": self.model_size,
                "compute_type": self.compute_type,
                "language_probability": info.language_probability,
                "segment_count": segment_count,
            },
        )

    def transcribe_batched(
        self,
        audio_path: str,
        language: str | None = None,
        batch_size: int = 16,
    ) -> TranscriptionResult:
        """
        Transcribe using batched inference (faster for long audio).

        Args:
            audio_path: Path to audio file
            language: Optional language hint
            batch_size: Batch size for parallel processing

        Returns:
            TranscriptionResult with transcription
        """
        self.initialize()

        try:
            from faster_whisper import BatchedInferencePipeline
        except ImportError:
            logger.warning("[FASTER-WHISPER] BatchedInferencePipeline not available, using standard transcription")
            return self.transcribe(audio_path, language)

        # Create batched model if not exists
        if self._batched_model is None:
            self._batched_model = BatchedInferencePipeline(model=self._model)

        logger.debug("Batched transcription", batch_size=batch_size)

        segments_generator, info = self._batched_model.transcribe(
            audio_path,
            language=language,
            batch_size=batch_size,
        )

        # Collect segments
        segments = []
        full_text_parts = []

        for seg in segments_generator:
            segments.append(
                TranscriptionSegment(
                    start_time=seg.start,
                    end_time=seg.end,
                    text=seg.text.strip(),
                    metadata={"id": seg.id if hasattr(seg, "id") else None},
                )
            )
            full_text_parts.append(seg.text)

        full_text = "".join(full_text_parts).strip()

        return TranscriptionResult(
            full_text=full_text,
            segments=segments,
            language=info.language,
            duration=segments[-1].end_time if segments else 0,
            metadata={
                "model": self.model_size,
                "batch_size": batch_size,
                "batched": True,
            },
        )

    def transcribe_with_timestamps(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Transcribe with detailed timestamps - same as transcribe for Faster-Whisper"""
        return self.transcribe(audio_path, language)

    def transcribe_batch(self, audio_paths: list[str], language: str | None = None) -> list[TranscriptionResult]:
        """Transcribe multiple audio files"""
        results = []
        for audio_path in audio_paths:
            result = self.transcribe(audio_path, language)
            results.append(result)
        return results

    def supports_video(self) -> bool:
        """Faster-Whisper supports video through audio extraction"""
        return True

    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> str:
        """Extract audio from video file"""
        from services.media import extract_audio_from_video

        return extract_audio_from_video(video_path, output_path, sample_rate=16000)

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes (same as Whisper - 99 languages)"""
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

    @property
    def model_info(self) -> dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "name": f"faster-whisper-{self.model_size}",
            "model_size": self.model_size,
            "compute_type": self.compute_type,
            "device": self.device,
            "backend": "CTranslate2",
            "loaded": self._model is not None,
        }

    @property
    def service_name(self) -> str:
        """Get the name of this service"""
        return f"Faster-Whisper ({self.model_size})"

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized"""
        return self._model is not None

    def cleanup(self) -> None:
        """Clean up model resources"""
        if self._model is not None:
            del self._model
            self._model = None
        if self._batched_model is not None:
            del self._batched_model
            self._batched_model = None

        # Clear CUDA cache if available
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        logger.info("[FASTER-WHISPER] Model cleaned up")
