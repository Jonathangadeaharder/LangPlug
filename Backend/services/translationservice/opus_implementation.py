"""
OPUS-MT Translation Service Implementation
Helsinki-NLP's OPUS-MT models for fast, efficient translation
"""

import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

from .interface import ITranslationService, TranslationResult

logger = logging.getLogger(__name__)


class OpusTranslationService(ITranslationService):
    """
    OPUS-MT implementation of translation service
    Fast, efficient models for specific language pairs
    """

    def __init__(
        self,
        model_name: str = "Helsinki-NLP/opus-mt-de-en",
        max_length: int = 512
    ):
        """
        Initialize OPUS-MT translation service

        Args:
            model_name: HuggingFace model name (e.g., Helsinki-NLP/opus-mt-de-en)
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        self.max_length = max_length
        self._translator = None
        self._model = None
        self._tokenizer = None

    def initialize(self) -> None:
        """Initialize the OPUS-MT model and tokenizer"""
        if self._translator is None:
            logger.info(f"Loading OPUS-MT model: {self.model_name}")

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

            # Create pipeline
            self._translator = pipeline(
                "translation",
                model=self._model,
                tokenizer=self._tokenizer,
                max_length=self.max_length
            )

            logger.info(f"OPUS-MT model loaded: {self.model_name}")

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """Translate a single text"""
        if not self.is_initialized:
            self.initialize()

        # OPUS-MT models are language-pair specific, so we don't need to specify languages
        result = self._translator(text)

        return TranslationResult(
            original_text=text,
            translated_text=result[0]["translation_text"],
            source_language=source_lang,
            target_language=target_lang,
            metadata={
                "model": self.model_name,
                "service": "OPUS-MT"
            }
        )

    def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str
    ) -> list[TranslationResult]:
        """Translate multiple texts in batch"""
        if not self.is_initialized:
            self.initialize()

        # Perform batch translation
        results = self._translator(texts)

        # Create TranslationResult objects
        translation_results = []
        for text, result in zip(texts, results, strict=False):
            translation_results.append(
                TranslationResult(
                    original_text=text,
                    translated_text=result["translation_text"],
                    source_language=source_lang,
                    target_language=target_lang,
                    metadata={
                        "model": self.model_name,
                        "service": "OPUS-MT"
                    }
                )
            )

        return translation_results

    def get_supported_languages(self) -> dict[str, str]:
        """Get dictionary of supported languages (varies by model)"""
        # This is model-specific - common OPUS models support these pairs
        return {
            "de": "German",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
        }

    def is_language_supported(self, lang_code: str) -> bool:
        """Check if a language is supported"""
        return lang_code in self.get_supported_languages()

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

    @property
    def service_name(self) -> str:
        """Get the name of this translation service"""
        return "OPUS-MT"

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized and ready"""
        return self._translator is not None