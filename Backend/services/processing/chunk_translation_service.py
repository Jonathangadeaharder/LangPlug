"""
ChunkTranslationService - Handle translation services and translation building
Extracted from chunk_processor.py for better separation of concerns
"""

import asyncio
import logging
from typing import Any

from tqdm import tqdm

from core.config import settings
from services.interfaces.translation_interface import IChunkTranslationService
from services.translationservice.factory import TranslationServiceFactory
from services.translationservice.interface import ITranslationService
from utils.srt_parser import SRTParser, SRTSegment

logger = logging.getLogger(__name__)


class ChunkTranslationError(Exception):
    """Exception for chunk translation errors"""

    pass


class ChunkTranslationService(IChunkTranslationService):
    """
    Service responsible for managing translation services and building translations
    """

    def __init__(self):
        self._translation_services: dict[tuple[str, str, str], ITranslationService] = {}

    def get_translation_service(
        self, source_lang: str, target_lang: str, quality: str = "standard"
    ) -> ITranslationService:
        """
        Get or create a translation service for the specified language pair

        Args:
            source_lang: Source language code
            target_lang: Target language code
            quality: Translation quality level

        Returns:
            Translation service instance
        """
        service_key = (source_lang, target_lang, quality)

        if service_key not in self._translation_services:
            # Calculate the correct OPUS model for this language pair
            # OPUS models follow pattern: Helsinki-NLP/opus-mt-{source}-{target}
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

            logger.info(
                f"Creating translation service: {source_lang} -> {target_lang} " f"(model: {model_name})"
            )

            self._translation_services[service_key] = TranslationServiceFactory.create_service(
                service_name="opus",  # Use OPUS service type
                model_name=model_name,  # Explicitly set model for language pair
            )

        return self._translation_services[service_key]

    async def build_translation_segments(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        srt_file_path: str,
        vocabulary: list,
        language_preferences: dict[str, Any],
    ) -> list[SRTSegment]:
        """
        Build translation segments for vocabulary words in SRT file

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            srt_file_path: Path to SRT subtitle file
            vocabulary: List of vocabulary words to translate
            language_preferences: User language preferences

        Returns:
            List of translation segments
        """
        task_progress[task_id].progress = 65.0
        task_progress[task_id].current_step = "Building translations..."
        task_progress[task_id].message = "Creating translated subtitle segments"

        if not vocabulary:
            logger.info("[CHUNK DEBUG] No vocabulary to translate, returning empty segments")
            return []

        # Parse the SRT file
        srt_parser = SRTParser()
        subtitle_segments = srt_parser.parse_file(srt_file_path)

        if not subtitle_segments:
            logger.warning(f"[CHUNK DEBUG] No subtitle segments found in {srt_file_path}")
            return []

        # Translate ALL segments (not just vocabulary segments)
        # The Frontend needs complete translations for all subtitles
        translation_segments = await self._build_translation_texts(
            task_id, task_progress, subtitle_segments, language_preferences
        )

        logger.info(f"[CHUNK DEBUG] Built {len(translation_segments)} translation segments")
        return translation_segments

    def _map_active_words_to_segments(
        self, vocabulary: list, subtitle_segments: list[SRTSegment]
    ) -> list[tuple[dict, SRTSegment]]:
        """
        Map active vocabulary words to their corresponding subtitle segments

        Args:
            vocabulary: List of vocabulary word dictionaries
            subtitle_segments: List of SRT segments

        Returns:
            List of (vocabulary_word, segment) tuples for active words
        """
        active_word_segments = []

        for word_info in vocabulary:
            if not isinstance(word_info, dict) or not word_info.get("active", False):
                continue

            word = word_info.get("word", "").lower()
            if not word:
                continue

            # Find segments containing this word
            for segment in subtitle_segments:
                if word in segment.text.lower():
                    active_word_segments.append((word_info, segment))
                    break

        logger.info(f"[CHUNK DEBUG] Found {len(active_word_segments)} active words in segments")
        return active_word_segments

    async def _build_translation_texts(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        subtitle_segments: list[SRTSegment],
        language_preferences: dict[str, Any],
    ) -> list[SRTSegment]:
        """
        Build translated text segments for all subtitle segments

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            subtitle_segments: List of subtitle segments to translate
            language_preferences: User language preferences

        Returns:
            List of translated SRT segments
        """
        source_lang = language_preferences.get("target", "de")
        target_lang = language_preferences.get("native", "en")

        logger.info(
            f"[TRANSLATION DEBUG] Building translations: {source_lang} -> {target_lang} "
            f"(preferences: {language_preferences})"
        )

        translation_service = self.get_translation_service(source_lang, target_lang)

        async def translate_with_progress(task_id=None, task_progress_dict=None):
            """Translate segments with progress tracking"""
            translation_segments = []
            batch_size = 5  # Process in small batches to yield to event loop

            for i, segment in enumerate(tqdm(subtitle_segments, desc="Translating segments", disable=False)):
                try:
                    # Update progress every segment to ensure smooth updates (65% -> 95%)
                    if task_id and task_progress_dict:
                        # Map translation progress (0-100%) to overall range (65-95%)
                        translation_pct = (i + 1) / len(subtitle_segments)
                        progress = int(65 + (30 * translation_pct))
                        task_progress_dict[task_id].progress = progress
                        task_progress_dict[task_id].current_step = "Building translations..."
                        task_progress_dict[task_id].message = f"Translating segment {i+1}/{len(subtitle_segments)}"

                    # Create translation segment
                    translation_result = translation_service.translate(segment.text, source_lang, target_lang)

                    translation_segment = SRTSegment(
                        index=segment.index,
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=translation_result.translated_text,
                    )

                    translation_segments.append(translation_segment)

                    # Yield to event loop every batch to allow FastAPI to respond to requests
                    if (i + 1) % batch_size == 0:
                        await asyncio.sleep(0.01)  # 10ms yield to event loop

                except Exception as e:
                    logger.error(f"Translation failed for segment {segment.index}: {e}")
                    continue

            # Update progress one final time before returning
            if task_id and task_progress_dict:
                task_progress_dict[task_id].progress = 95
                task_progress_dict[task_id].current_step = "Building translations..."
                task_progress_dict[task_id].message = "Translation completed"

            return translation_segments

        return await translate_with_progress(task_id, task_progress)

    def segments_overlap(
        self, seg1_start: float, seg1_end: float, seg2_start: float, seg2_end: float, threshold: float = 0.5
    ) -> bool:
        """
        Check if two time segments overlap significantly

        Args:
            seg1_start: Start time of first segment
            seg1_end: End time of first segment
            seg2_start: Start time of second segment
            seg2_end: End time of second segment
            threshold: Minimum overlap ratio to consider significant

        Returns:
            True if segments overlap significantly
        """
        overlap_start = max(seg1_start, seg2_start)
        overlap_end = min(seg1_end, seg2_end)
        overlap_duration = max(0, overlap_end - overlap_start)

        seg1_duration = seg1_end - seg1_start
        seg2_duration = seg2_end - seg2_start
        min_duration = min(seg1_duration, seg2_duration)

        if min_duration == 0:
            return False

        overlap_ratio = overlap_duration / min_duration
        return overlap_ratio >= threshold
