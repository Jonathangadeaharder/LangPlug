"""
NLLB-200 Translation Service Implementation
Facebook/Meta's No Language Left Behind model
"""

from typing import ClassVar

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

from core.config.logging_config import get_logger

from .interface import ITranslationService, TranslationResult

logger = get_logger(__name__)


class NLLBTranslationService(ITranslationService):
    """
    NLLB-200 implementation of translation service
    Supports 200+ languages with high quality translation
    """

    # Language code mappings for NLLB
    LANGUAGE_CODES: ClassVar[dict[str, str]] = {
        "en": "eng_Latn",  # English
        "de": "deu_Latn",  # German
        "es": "spa_Latn",  # Spanish
        "fr": "fra_Latn",  # French
        "it": "ita_Latn",  # Italian
        "pt": "por_Latn",  # Portuguese
        "ru": "rus_Cyrl",  # Russian
        "zh": "zho_Hans",  # Chinese (Simplified)
        "ja": "jpn_Jpan",  # Japanese
        "ko": "kor_Hang",  # Korean
        "ar": "arb_Arab",  # Arabic
        "hi": "hin_Deva",  # Hindi
        "nl": "nld_Latn",  # Dutch
        "pl": "pol_Latn",  # Polish
        "tr": "tur_Latn",  # Turkish
        "sv": "swe_Latn",  # Swedish
        "no": "nob_Latn",  # Norwegian
        "da": "dan_Latn",  # Danish
        "fi": "fin_Latn",  # Finnish
        "cs": "ces_Latn",  # Czech
        "hu": "hun_Latn",  # Hungarian
        "el": "ell_Grek",  # Greek
        "he": "heb_Hebr",  # Hebrew
        "th": "tha_Thai",  # Thai
        "vi": "vie_Latn",  # Vietnamese
        "id": "ind_Latn",  # Indonesian
        "ms": "zsm_Latn",  # Malay
    }

    def __init__(
        self, model_name: str = "facebook/nllb-200-distilled-600M", device: str | None = None, max_length: int = 512
    ):
        """
        Initialize NLLB translation service

        Args:
            model_name: HuggingFace model name
            device: Device to use ('cuda', 'cpu', or None for auto)
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        self.max_length = max_length
        self._translator = None
        self._model = None
        self._tokenizer = None

        # Auto-detect device if not specified
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
            self.device_str = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = 0 if device == "cuda" else -1
            self.device_str = device

    def initialize(self) -> None:
        """Initialize the NLLB model and tokenizer"""
        if self._translator is None:
            from core.gpu_utils import check_cuda_availability

            # Check CUDA availability and configure device
            cuda_available = check_cuda_availability("NLLB")

            if cuda_available:
                logger.info("GPU available for NLLB", device=torch.cuda.get_device_name(0))
                self.device = 0
                self.device_str = "cuda"
            else:
                self.device = -1
                self.device_str = "cpu"

            logger.info("Loading NLLB model", model=self.model_name)

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device_str == "cuda" else torch.float32,
                low_cpu_mem_usage=True,
            )

            # Create pipeline
            self._translator = pipeline(
                "translation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=self.device,
                max_length=self.max_length,
            )

            logger.info("NLLB model loaded", device=self.device_str)

    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate a single text"""
        if not self.is_initialized:
            self.initialize()

        # Convert language codes to NLLB format
        src_lang = self.LANGUAGE_CODES.get(source_lang, source_lang)
        tgt_lang = self.LANGUAGE_CODES.get(target_lang, target_lang)

        # Perform translation
        result = self._translator(text, src_lang=src_lang, tgt_lang=tgt_lang)

        return TranslationResult(
            original_text=text,
            translated_text=result[0]["translation_text"],
            source_language=source_lang,
            target_language=target_lang,
            metadata={"model": self.model_name, "device": self.device_str},
        )

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[TranslationResult]:
        """Translate multiple texts in batch"""
        if not self.is_initialized:
            self.initialize()

        # Convert language codes to NLLB format
        src_lang = self.LANGUAGE_CODES.get(source_lang, source_lang)
        tgt_lang = self.LANGUAGE_CODES.get(target_lang, target_lang)

        # Perform batch translation
        results = self._translator(texts, src_lang=src_lang, tgt_lang=tgt_lang)

        # Create TranslationResult objects
        translation_results = []
        for text, result in zip(texts, results, strict=False):
            translation_results.append(
                TranslationResult(
                    original_text=text,
                    translated_text=result["translation_text"],
                    source_language=source_lang,
                    target_language=target_lang,
                    metadata={"model": self.model_name, "device": self.device_str},
                )
            )

        return translation_results

    def get_supported_languages(self) -> dict[str, str]:
        """Get dictionary of supported languages"""
        return {
            "en": "English",
            "de": "German",
            "es": "Spanish",
            "fr": "French",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese (Simplified)",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "cs": "Czech",
            "hu": "Hungarian",
            "el": "Greek",
            "he": "Hebrew",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
        }

    def is_language_supported(self, lang_code: str) -> bool:
        """Check if a language is supported"""
        return lang_code in self.LANGUAGE_CODES or lang_code in self.LANGUAGE_CODES.values()

    def cleanup(self) -> None:
        """Clean up resources and unload models"""
        if self._translator is not None:
            del self._translator
            self._translator = None

        if self._model is not None:
            del self._model
            self._model = None

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        # Clear GPU cache if using CUDA
        if self.device_str == "cuda":
            torch.cuda.empty_cache()

    @property
    def service_name(self) -> str:
        """Get the name of this translation service"""
        return "NLLB-200"

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized and ready"""
        return self._translator is not None
