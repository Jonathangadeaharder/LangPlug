"""
Translation handling service
Extracted from api/routes/processing.py for better separation of concerns
"""

import time
from pathlib import Path
from typing import Any

from api.models.processing import ProcessingStatus
from core.config.logging_config import get_logger
from services.translationservice.interface import ITranslationService
from utils.srt_parser import SRTParser, SRTSegment

logger = get_logger(__name__)


class TranslationHandler:
    """Handles translation operations for subtitle processing"""

    def __init__(self, translation_service: ITranslationService):
        self.translation_service = translation_service

    async def translate_subtitles(
        self,
        srt_path: str,
        task_id: str,
        task_progress: dict[str, Any],
        source_language: str = "de",
        target_language: str = "en",
        user_id: str | None = None,
    ) -> str:
        """
        Translate subtitles with progress tracking

        Args:
            srt_path: Path to source SRT file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            source_language: Source language code
            target_language: Target language code
            user_id: Optional user ID for personalized translation

        Returns:
            Path to translated SRT file
        """
        try:
            logger.info("Starting translation task", task_id=task_id)

            # Initialize progress tracking
            task_progress[task_id] = ProcessingStatus(
                status="processing",
                progress=0.0,
                current_step="Starting translation...",
                message="Loading subtitle file",
                started_at=int(time.time()),
            )

            # Step 1: Load and parse SRT file
            segments = await self._load_subtitles(srt_path, task_progress, task_id)

            # Step 2: Prepare for translation (10% progress)
            await self._prepare_translation(task_progress, task_id, source_language, target_language)

            # Step 3: Translate segments (10-90% progress)
            translated_segments = await self._translate_segments(
                segments, task_progress, task_id, source_language, target_language, user_id
            )

            # Step 4: Save translated subtitles (90-100% progress)
            output_path = await self._save_translated_subtitles(
                translated_segments, srt_path, task_progress, task_id, target_language
            )

            # Mark as complete
            task_progress[task_id].status = "completed"
            task_progress[task_id].progress = 100.0
            task_progress[task_id].message = "Translation completed successfully"
            task_progress[task_id].result_path = output_path
            task_progress[task_id].completed_at = int(time.time())

            logger.info("Translation task completed", task_id=task_id)
            return output_path

        except Exception as e:
            logger.error("Translation task failed", task_id=task_id, error=str(e))
            task_progress[task_id].status = "failed"
            task_progress[task_id].error = str(e)
            task_progress[task_id].message = f"Translation failed: {e!s}"
            raise

    async def _load_subtitles(self, srt_path: str, task_progress: dict[str, Any], task_id: str) -> list[SRTSegment]:
        """Load and parse SRT file"""
        task_progress[task_id].progress = 5.0
        task_progress[task_id].current_step = "Loading subtitles..."
        task_progress[task_id].message = "Reading subtitle file"

        srt_file = Path(srt_path)
        if not srt_file.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")

        segments = SRTParser.parse_file(str(srt_file))

        if not segments:
            raise ValueError("No subtitle segments found in file")

        logger.debug("Loaded subtitle segments", count=len(segments))
        return segments

    async def _prepare_translation(
        self, task_progress: dict[str, Any], task_id: str, source_language: str, target_language: str
    ) -> None:
        """Prepare translation service"""
        task_progress[task_id].progress = 10.0
        task_progress[task_id].current_step = "Preparing translation..."
        task_progress[task_id].message = f"Setting up {source_language} → {target_language} translation"

        # Initialize translation model if needed
        await self.translation_service.initialize(source_language, target_language)

    async def _translate_segments(
        self,
        segments: list[SRTSegment],
        task_progress: dict[str, Any],
        task_id: str,
        source_language: str,
        target_language: str,
        user_id: str | None = None,
    ) -> list[SRTSegment]:
        """Translate all subtitle segments"""
        translated_segments = []
        total_segments = len(segments)

        for i, segment in enumerate(segments):
            # Update progress (10% to 90% range)
            progress = 10.0 + (80.0 * i / total_segments)
            task_progress[task_id].progress = progress
            task_progress[task_id].current_step = "Translating..."
            task_progress[task_id].message = f"Translating segment {i + 1}/{total_segments}"

            # Translate the text
            translated_text = await self.translation_service.translate(
                segment.text,
                source_language=source_language,
                target_language=target_language,
                context={
                    "user_id": user_id,
                    "segment_index": segment.index,
                    "timestamp": f"{segment.start_time}-{segment.end_time}",
                },
            )

            # Create translated segment
            translated_segment = SRTSegment(
                index=segment.index, start_time=segment.start_time, end_time=segment.end_time, text=translated_text
            )
            translated_segments.append(translated_segment)

        return translated_segments

    async def _save_translated_subtitles(
        self,
        segments: list[SRTSegment],
        original_path: str,
        task_progress: dict[str, Any],
        task_id: str,
        target_language: str,
    ) -> str:
        """Save translated subtitles to file"""
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Saving translation..."
        task_progress[task_id].message = "Creating translated subtitle file"

        # Generate output filename
        original_file = Path(original_path)
        output_file = original_file.parent / f"{original_file.stem}.{target_language}.srt"

        # Write SRT content
        srt_content = SRTParser.segments_to_srt(segments)
        output_file.write_text(srt_content, encoding="utf-8")

        logger.debug("Saved translated subtitles", path=str(output_file))
        return str(output_file)

    async def batch_translate(
        self, texts: list[str], source_language: str, target_language: str, batch_size: int = 10
    ) -> list[str]:
        """
        Translate multiple texts in batches for efficiency

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            batch_size: Number of texts to translate at once

        Returns:
            List of translated texts
        """
        translated = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_translations = await self.translation_service.translate_batch(
                batch, source_language=source_language, target_language=target_language
            )
            translated.extend(batch_translations)

        return translated

    def estimate_duration(self, srt_path: str, source_language: str, target_language: str) -> int:
        """
        Estimate translation duration in seconds

        Args:
            srt_path: Path to SRT file
            source_language: Source language
            target_language: Target language

        Returns:
            Estimated duration in seconds

        Raises:
            Exception: If SRT file cannot be parsed
        """
        segments = SRTParser.parse_file(srt_path)
        # Estimate: 1 second per segment
        return max(30, len(segments))

    async def validate_languages(self, source_language: str, target_language: str) -> bool:
        """
        Validate that language pair is supported

        Args:
            source_language: Source language code
            target_language: Target language code

        Returns:
            True if language pair is supported
        """
        supported_pairs = await self.translation_service.get_supported_languages()
        return (source_language, target_language) in supported_pairs
