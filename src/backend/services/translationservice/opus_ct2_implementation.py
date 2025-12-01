"""
CTranslate2-Optimized OPUS-MT Translation Service Implementation

Uses CTranslate2 for significantly faster inference:
- GPU: 9x faster than Transformers (9296 vs 1022 tokens/sec)
- CPU: 4.7x faster than Transformers (696 vs 147 tokens/sec)
- 75% less memory usage
- INT8/FP16 quantization support

See: https://github.com/OpenNMT/CTranslate2
"""

import tempfile
from pathlib import Path
from typing import Any

from core.config.logging_config import get_logger

from .interface import ITranslationService, TranslationResult

logger = get_logger(__name__)


class OpusCT2TranslationService(ITranslationService):
    """
    CTranslate2-optimized OPUS-MT implementation.

    Benefits over standard Transformers:
    - Up to 9x faster translation on GPU
    - Up to 4.7x faster translation on CPU
    - 75% less memory usage
    - INT8/FP16 quantization for even better performance
    """

    # Compute types in order of performance (GPU)
    GPU_COMPUTE_TYPES = ["float16", "int8_float16", "int8", "float32"]
    # Compute types for CPU
    CPU_COMPUTE_TYPES = ["int8", "int16", "float32"]

    def __init__(
        self,
        model_name: str = "Helsinki-NLP/opus-mt-de-en",
        device: str | None = None,
        compute_type: str | None = None,
        inter_threads: int = 1,
        intra_threads: int = 4,
    ):
        """
        Initialize CTranslate2 OPUS-MT translation service.

        Args:
            model_name: HuggingFace OPUS-MT model name
            device: Device to use ('cuda', 'cpu', or 'auto')
            compute_type: Quantization type ('float16', 'int8', 'int8_float16', etc.)
            inter_threads: Number of workers for parallel translations
            intra_threads: Number of threads per worker (CPU only)
        """
        self.model_name = model_name
        self.device = device or "auto"
        self._compute_type = compute_type
        self.inter_threads = inter_threads
        self.intra_threads = intra_threads

        self._translator = None
        self._tokenizer = None
        self._model_path = None

    @property
    def compute_type(self) -> str:
        """Get the compute type, auto-selecting based on device"""
        if self._compute_type:
            return self._compute_type
        # Auto-select best compute type
        if self.device == "cuda":
            return "float16"  # Best for GPU
        return "int8"  # Best for CPU

    def _get_or_convert_model(self) -> str:
        """Get converted CTranslate2 model path, converting if needed."""
        import ctranslate2

        # Cache directory for converted models
        cache_dir = Path(tempfile.gettempdir()) / "ctranslate2_models"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Model-specific cache path
        model_safe_name = self.model_name.replace("/", "_").replace("-", "_")
        model_dir = cache_dir / f"{model_safe_name}_ct2"

        if model_dir.exists() and (model_dir / "model.bin").exists():
            logger.debug("Using cached CT2 model", path=str(model_dir))
            return str(model_dir)

        logger.info("Converting model to CTranslate2 format", source=self.model_name)

        # Convert the model
        try:
            ct2_converter = ctranslate2.converters.TransformersConverter(self.model_name)
            ct2_converter.convert(
                str(model_dir),
                quantization="float16",  # Convert with FP16 for smaller size
                force=True,
            )
            logger.info("Model converted to CT2 format")
        except Exception as e:
            logger.error("CT2 conversion failed", error=str(e))
            raise

        return str(model_dir)

    def initialize(self) -> None:
        """Initialize the CTranslate2 translator"""
        if self._translator is not None:
            return

        try:
            import ctranslate2
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "ctranslate2 or transformers not installed. Install with: pip install ctranslate2 transformers"
            ) from e

        from core.gpu_utils import check_cuda_availability

        # Check CUDA availability
        cuda_available = check_cuda_availability("OPUS-CT2")

        # Determine device
        if self.device == "auto":
            self.device = "cuda" if cuda_available else "cpu"
        elif self.device == "cuda" and not cuda_available:
            logger.warning("[OPUS-CT2] CUDA requested but unavailable, falling back to CPU")
            self.device = "cpu"

        # Adjust compute type for device
        compute_type = self.compute_type
        if self.device == "cpu" and compute_type in ("float16", "int8_float16"):
            logger.warning("Compute type not supported on CPU, using int8", requested=compute_type)
            compute_type = "int8"

        logger.info("Loading OPUS-CT2 model", model=self.model_name, device=self.device)

        # Get or convert the model
        model_path = self._get_or_convert_model()
        self._model_path = model_path

        # Load tokenizer from original model
        logger.debug("Loading tokenizer", model=self.model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Create CTranslate2 translator
        device_index = 0 if self.device == "cuda" else -1

        self._translator = ctranslate2.Translator(
            model_path,
            device=self.device,
            device_index=device_index if self.device == "cuda" else 0,
            compute_type=compute_type,
            inter_threads=self.inter_threads,
            intra_threads=self.intra_threads,
        )

        logger.info("OPUS-CT2 model loaded")
        if self.device == "cuda":
            import torch

            logger.debug("Using GPU", device=torch.cuda.get_device_name(0))

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate a single text"""
        results = self.translate_batch([text], source_lang, target_lang)
        return results[0]

    def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        beam_size: int = 2,
        max_batch_size: int = 64,
    ) -> list[TranslationResult]:
        """
        Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            beam_size: Beam search size (higher = better quality, slower)
            max_batch_size: Maximum batch size for parallel processing
        """
        if not self.is_initialized:
            self.initialize()

        # Tokenize using the proper method for Marian models
        # Convert text to token IDs, then to token strings for CTranslate2
        tokenized = []
        for text in texts:
            tokens = self._tokenizer.encode(text, add_special_tokens=True)
            token_strs = self._tokenizer.convert_ids_to_tokens(tokens)
            tokenized.append(token_strs)

        # Translate with CTranslate2
        results = self._translator.translate_batch(
            tokenized,
            beam_size=beam_size,
            max_batch_size=max_batch_size,
            return_scores=False,
            max_decoding_length=256,
        )

        # Decode and create results
        translation_results = []
        for text, result in zip(texts, results, strict=False):
            # Decode tokens back to text
            translated_tokens = result.hypotheses[0]
            # Convert tokens to IDs then decode
            token_ids = self._tokenizer.convert_tokens_to_ids(translated_tokens)
            translated_text = self._tokenizer.decode(token_ids, skip_special_tokens=True)

            translation_results.append(
                TranslationResult(
                    original_text=text,
                    translated_text=translated_text,
                    source_language=source_lang,
                    target_language=target_lang,
                    metadata={
                        "model": self.model_name,
                        "service": "OPUS-CT2",
                        "device": self.device,
                        "compute_type": self.compute_type,
                    },
                )
            )

        return translation_results

    def get_supported_languages(self) -> dict[str, str]:
        """Get dictionary of supported languages"""
        return {
            "de": "German",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "zh": "Chinese",
        }

    def is_language_supported(self, lang_code: str) -> bool:
        """Check if a language is supported"""
        return lang_code in self.get_supported_languages()

    def cleanup(self) -> None:
        """Clean up resources"""
        if self._translator is not None:
            del self._translator
            self._translator = None

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        # Clear CUDA cache
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        logger.info("[OPUS-CT2] Model cleaned up")

    @property
    def service_name(self) -> str:
        """Get the name of this translation service"""
        return f"OPUS-CT2 ({self.model_name.split('/')[-1]})"

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized"""
        return self._translator is not None

    @property
    def model_info(self) -> dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "name": self.model_name,
            "device": self.device,
            "compute_type": self.compute_type,
            "backend": "CTranslate2",
            "loaded": self._translator is not None,
        }
