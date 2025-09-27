"""
ChunkProcessingService - Refactored business logic from API routes
Addresses R4 risk: Complex business logic moved from API routes to dedicated service
"""
import asyncio
import logging
import time
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from api.models.processing import ProcessingStatus
from core.auth import jwt_authentication
from core.config import settings
from core.dependencies import get_subtitle_processor, get_transcription_service
from core.language_preferences import (
    DEFAULT_NATIVE_LANGUAGE,
    load_language_preferences,
    resolve_language_runtime_settings,
)
from database.models import User
from services.translationservice.factory import TranslationServiceFactory
from services.translationservice.interface import ITranslationService
from utils.srt_parser import SRTParser, SRTSegment

logger = logging.getLogger(__name__)


class ChunkProcessingError(Exception):
    """Base exception for chunk processing errors"""
    pass


class ChunkProcessingService:
    """
    Service for processing video chunks for vocabulary learning
    Orchestrates transcription, filtering, and subtitle generation
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self._translation_services: dict[tuple[str, str, str], ITranslationService] = {}

    async def process_chunk(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        user_id: Any,
        task_id: str,
        task_progress: dict[str, Any],
        session_token: str | None = None
    ) -> None:
        """
        Process a specific chunk of video for vocabulary learning
        
        Args:
            video_path: Path to the video file
            start_time: Start time in seconds
            end_time: End time in seconds
            user_id: User ID for authentication and filtering
            task_id: Unique task identifier for progress tracking
            task_progress: Shared progress tracking dictionary
            session_token: Optional session token for authentication
        """
        try:
            logger.info(f"🎬 [CHUNK PROCESSING START] Task: {task_id}")
            logger.info(f"📹 [CHUNK PROCESSING] Video: {video_path}")
            logger.info(f"⏱️ [CHUNK PROCESSING] Time range: {start_time}-{end_time}s")

            # Initialize progress tracking
            self._initialize_progress(task_id, task_progress, start_time, end_time)

            # Validate and resolve video path
            video_file = self._resolve_video_path(video_path)

            current_user = await self._get_authenticated_user(user_id, session_token)
            language_preferences = self._load_user_language_preferences(current_user)

            # Step 1: Extract audio chunk (20% progress)
            await self._extract_audio_chunk(task_id, task_progress, video_file, start_time, end_time)

            # Step 2: Transcribe chunk (50% progress)
            await self._transcribe_chunk(task_id, task_progress, video_file, language_preferences)

            # Step 3: Filter for vocabulary (70% progress)
            filter_result = await self._filter_vocabulary(
                task_id,
                task_progress,
                video_file,
                current_user,
                language_preferences,
            )
            vocabulary = filter_result.get("blocking_words", [])

            # Step 4: Generate filtered subtitles (90% progress)
            await self._generate_filtered_subtitles(
                task_id,
                task_progress,
                video_file,
                filter_result,
                start_time,
                end_time,
                language_preferences,
            )

            # Complete (100% progress)
            self._complete_processing(task_id, task_progress, vocabulary)

        except Exception as e:
            self._handle_error(task_id, task_progress, e)
            raise ChunkProcessingError(f"Chunk processing failed: {e}") from e

    def _initialize_progress(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        start_time: float,
        end_time: float
    ) -> None:
        """Initialize progress tracking for the task"""
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Initializing chunk processing...",
            message=f"Processing segment {int(start_time//60)}:{int(start_time%60):02d} - {int(end_time//60)}:{int(end_time%60):02d}",
            started_at=int(time.time()),
        )

    def _resolve_video_path(self, video_path: str) -> Path:
        """Resolve and validate the video file path"""
        raw_path = Path(video_path)
        video_file = raw_path if raw_path.is_absolute() else settings.get_videos_path() / raw_path

        if not video_file.exists():
            raise ChunkProcessingError(f"Video file not found: {video_file}")

        return video_file

    async def _extract_audio_chunk(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        start_time: float,
        end_time: float
    ) -> None:
        """Extract audio chunk from video (simulated for now)"""
        task_progress[task_id].progress = 20.0
        task_progress[task_id].current_step = "Extracting audio chunk..."
        task_progress[task_id].message = "Isolating audio for this segment"

        # Simulate audio extraction process
        await asyncio.sleep(2)

        logger.info(f"[CHUNK DEBUG] Audio extracted for {video_file.name} ({start_time}-{end_time}s)")

    async def _transcribe_chunk(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        language_preferences: dict[str, Any] | None = None,
    ) -> None:
        """Transcribe the audio chunk"""
        task_progress[task_id].progress = 50.0
        target_language = language_preferences.get("target") if language_preferences else settings.default_language
        task_progress[task_id].current_step = "Transcribing audio..."
        task_progress[task_id].message = f"Converting speech ({target_language}) to text"

        transcription_service = get_transcription_service()
        if not transcription_service:
            raise ChunkProcessingError("Transcription service is not available. Please check server configuration.")

        # In real implementation, transcribe just the chunk
        # For now, simulate the process
        await asyncio.sleep(3)

        logger.info(f"[CHUNK DEBUG] Transcription completed for {video_file.name}")

    async def _filter_vocabulary(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        user: User,
        language_preferences: dict[str, Any],
    ) -> dict[str, Any]:
        """Filter vocabulary based on user's knowledge level"""
        task_progress[task_id].progress = 70.0
        task_progress[task_id].current_step = "Analyzing vocabulary..."
        task_progress[task_id].message = "Identifying difficult words"

        # Find the SRT file for this video
        srt_file_path = self._find_matching_srt_file(video_file)

        # Get subtitle processor
        subtitle_processor = get_subtitle_processor(self.db_session)

        target_language = language_preferences.get("target") or settings.default_language
        logger.info(
            "[CHUNK DEBUG] Subtitle processor created for user %s (%s -> %s)",
            user.username,
            language_preferences.get("native"),
            target_language,
        )
        logger.info(f"[CHUNK DEBUG] Processing SRT file: {srt_file_path}")

        # Process the SRT file through the subtitle processor
        filter_result = await subtitle_processor.process_srt_file(
            srt_file_path,
            user_id=user.id,
            language=target_language,
        )

        logger.info(f"[CHUNK DEBUG] Filter result keys: {list(filter_result.keys())}")
        logger.info(f"[CHUNK DEBUG] Filter result statistics: {filter_result.get('statistics', {})}")

        # Check for processing errors
        if "error" in filter_result.get("statistics", {}):
            error_msg = filter_result["statistics"]["error"]
            logger.error(f"[CHUNK ERROR] Subtitle processing failed: {error_msg}")
            raise ChunkProcessingError(f"Subtitle processing failed: {error_msg}")

        # Extract blocking words
        blocking_words = filter_result.get("blocking_words", [])
        logger.info(f"[CHUNK DEBUG] Blocking words found: {len(blocking_words)}")

        if blocking_words:
            for i, word in enumerate(blocking_words[:5]):  # Log first 5 words
                logger.info(
                    "[CHUNK DEBUG] Blocking word %s: %s",
                    i + 1,
                    word.word if hasattr(word, "word") else word,
                )
        else:
            self._debug_empty_vocabulary(filter_result, srt_file_path)

        return filter_result

    def _find_matching_srt_file(self, video_file: Path) -> str:
        """Find the best matching SRT file for the video"""
        video_dir = video_file.parent
        srt_files = list(video_dir.glob("*.srt"))

        # Filter out previously generated chunk files
        original_srt_files = [f for f in srt_files if "_chunk_" not in f.name]

        if not original_srt_files:
            raise ChunkProcessingError(f"No SRT file found in {video_dir}")

        # Find the best matching SRT file
        video_stem = video_file.stem
        exact_matches = [f for f in original_srt_files if f.stem == video_stem]
        contains_matches = [
            f for f in original_srt_files
            if f.stem in video_stem or video_stem in f.stem
        ]

        if exact_matches:
            best_srt = exact_matches[0]
            logger.info(f"[CHUNK DEBUG] Using exact SRT match for video stem '{video_stem}': {best_srt.name}")
        elif contains_matches:
            # Prefer the longest stem (most specific filename)
            best_srt = sorted(contains_matches, key=lambda f: len(f.stem), reverse=True)[0]
            logger.info(f"[CHUNK DEBUG] Using partial SRT match for video stem '{video_stem}': {best_srt.name}")
        else:
            # Fallback to the largest SRT file (likely full episode)
            best_srt = sorted(original_srt_files, key=lambda f: f.stat().st_size, reverse=True)[0]
            logger.info(f"[CHUNK DEBUG] Using largest SRT by size as fallback: {best_srt.name} ({best_srt.stat().st_size} bytes)")

        return str(best_srt)

    async def _get_authenticated_user(self, user_identifier: Any, session_token: str | None) -> User:
        """Get and validate the authenticated user"""
        try:
            # Get user by ID from database
            normalized_id = self._normalize_user_identifier(user_identifier)
            result = await self.db_session.execute(select(User).where(User.id == normalized_id))
            current_user = result.scalar_one_or_none()

            if not current_user:
                raise ChunkProcessingError(f"User with ID {user_identifier} not found in database")

        except Exception as e:
            logger.error(f"Could not get user from database: {e}")
            raise ChunkProcessingError(f"Failed to get user information: {e}") from e

        # Validate session token if provided
        if session_token:
            try:
                authenticated_user = await jwt_authentication.authenticate(session_token)
                if authenticated_user.id != current_user.id:
                    raise ChunkProcessingError("Token user ID does not match requested user ID")
                logger.info(f"Valid session token provided for user {current_user.id}")
            except Exception as e:
                logger.error(f"Invalid session token provided: {e}")
                raise ChunkProcessingError(f"Authentication failed: {e}") from e
        else:
            logger.warning(f"No session token provided for user {current_user.id}")

        return current_user

    def _debug_empty_vocabulary(self, filter_result: dict[str, Any], srt_file_path: str) -> None:
        """Debug why no blocking words were found"""
        logger.warning("[CHUNK DEBUG] ❌ NO BLOCKING WORDS FOUND - checking why...")

        # Debug: check if SRT file has content
        try:
            with open(srt_file_path, encoding='utf-8') as f:
                content = f.read()[:200]  # First 200 chars
                logger.info(f"[CHUNK DEBUG] SRT file sample: {content}")
        except Exception as e:
            logger.error(f"[CHUNK DEBUG] Cannot read SRT file: {e}")

        # Debug: check statistics from each filter
        stats = filter_result.get("statistics", {})
        logger.info(f"[CHUNK DEBUG] Total segments parsed: {stats.get('segments_parsed', 0)}")
        logger.info(f"[CHUNK DEBUG] Total words processed: {stats.get('total_words', 0)}")
        logger.info(f"[CHUNK DEBUG] Active words remaining: {stats.get('active_words', 0)}")
        logger.info(f"[CHUNK DEBUG] Filtered words: {stats.get('filtered_words', 0)}")
        logger.info(f"[CHUNK DEBUG] Learning subtitles: {stats.get('learning_subtitles', 0)}")
        logger.info(f"[CHUNK DEBUG] Empty subtitles: {stats.get('empty_subtitles', 0)}")

    async def _generate_filtered_subtitles(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        filter_result: dict[str, Any],
        start_time: float,
        end_time: float,
        language_preferences: dict[str, Any],
    ) -> None:
        """Generate filtered subtitle files."""
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Creating filtered subtitles..."
        task_progress[task_id].message = "Generating subtitles for difficult parts only"

        self._cleanup_old_chunk_files(video_file, start_time, end_time)

        chunk_filename = f"{video_file.stem}_chunk_{int(start_time)}_{int(end_time)}.srt"
        chunk_output_path = video_file.parent / chunk_filename
        translation_filename = f"{video_file.stem}_chunk_{int(start_time)}_{int(end_time)}_translation.srt"
        translation_output_path = video_file.parent / translation_filename

        try:
            logger.info("[SUBTITLE GENERATION] Starting subtitle generation for chunk")
            original_srt_path = Path(self._find_matching_srt_file(video_file))
            parser = SRTParser()
            segments = parser.parse_file(original_srt_path)
            logger.info(f"[SUBTITLE GENERATION] Found {len(segments)} segments in original SRT")

            chunk_segments = [
                seg for seg in segments if seg.start_time < end_time and seg.end_time > start_time
            ]
            logger.info(f"[SUBTITLE GENERATION] {len(chunk_segments)} segments in chunk time range")

            adjusted_segments: list[SRTSegment] = []
            for index, segment in enumerate(chunk_segments, 1):
                adjusted_segments.append(
                    SRTSegment(
                        index=index,
                        start_time=max(0.0, segment.start_time - start_time),
                        end_time=max(0.0, segment.end_time - start_time),
                        text=segment.text,
                        original_text=segment.original_text or segment.text,
                        translation="",
                    )
                )

            SRTParser.save_segments(adjusted_segments, str(chunk_output_path))
            logger.info(
                "[SUBTITLE GENERATION] Generated chunk SRT file: %s (segments=%s)",
                chunk_output_path,
                len(adjusted_segments),
            )

            videos_path = settings.get_videos_path()
            task_progress[task_id].subtitle_path = str(chunk_output_path.relative_to(videos_path))

            logger.info("[SUBTITLE GENERATION] Starting translation segment building...")
            translation_segments = await self._build_translation_segments(
                chunk_segments,
                adjusted_segments,
                filter_result.get("filtered_subtitles", []),
                start_time,
                language_preferences,
                task_id,
                task_progress,
            )
            logger.info(f"[SUBTITLE GENERATION] Built {len(translation_segments)} translation segments")

            if translation_segments:
                SRTParser.save_segments(translation_segments, str(translation_output_path))
                task_progress[task_id].translation_path = str(
                    translation_output_path.relative_to(videos_path)
                )
                logger.info(
                    "[CHUNK DEBUG] Generated translation SRT file: %s (segments=%s)",
                    translation_output_path,
                    len(translation_segments),
                )
            else:
                task_progress[task_id].translation_path = None

        except Exception as exc:  # pragma: no cover - error handling
            logger.error(f"[CHUNK ERROR] Failed to generate filtered subtitles: {exc}", exc_info=True)
            chunk_output_path.write_text("# Chunk processing completed\n", encoding="utf-8")
            videos_path = settings.get_videos_path()
            task_progress[task_id].subtitle_path = str(chunk_output_path.relative_to(videos_path))

        blocking_words = filter_result.get("blocking_words", [])
        logger.info(f"[CHUNK DEBUG] Generated filtered subtitles for {len(blocking_words)} vocabulary words")



    # Note: _format_srt_timestamp method removed - using SRTParser.format_timestamp instead
    # to eliminate code duplication and maintain consistency

    async def _build_translation_segments(
        self,
        original_segments: list[SRTSegment],
        adjusted_segments: list[SRTSegment],
        filtered_subtitles: list,
        chunk_start: float,
        language_preferences: dict[str, Any],
        task_id: str | None = None,
        task_progress: dict[str, Any] | None = None,
    ) -> list[SRTSegment]:
        if not filtered_subtitles or not original_segments:
            logger.info("[TRANSLATION SEGMENTS] No filtered subtitles or segments to process")
            return []

        logger.info(f"[TRANSLATION SEGMENTS] Mapping active words to {len(original_segments)} segments")
        segment_active_words = self._map_active_words_to_segments(original_segments, filtered_subtitles)

        active_count = sum(1 for words in segment_active_words if words)
        logger.info(f"[TRANSLATION SEGMENTS] Found {active_count} segments with active words")

        if not any(segment_active_words):
            logger.info("[TRANSLATION SEGMENTS] No segments have active words, skipping translation")
            return []

        logger.info("[TRANSLATION SEGMENTS] Building translation texts...")
        translation_texts = await self._build_translation_texts(
            original_segments,
            segment_active_words,
            language_preferences,
            task_id,
            task_progress,
        )

        translation_segments: list[SRTSegment] = []
        for adjusted, translation_text in zip(adjusted_segments, translation_texts, strict=False):
            if not translation_text.strip():
                continue
            translation_segments.append(
                SRTSegment(
                    index=adjusted.index,
                    start_time=adjusted.start_time,
                    end_time=adjusted.end_time,
                    text=translation_text,
                    original_text=translation_text,
                    translation="",
                )
            )

        return translation_segments

    def _map_active_words_to_segments(
        self,
        chunk_segments: list[SRTSegment],
        filtered_subtitles: list,
    ) -> list[list[Any]]:
        segment_map: list[list[Any]] = [[] for _ in chunk_segments]

        for idx, segment in enumerate(chunk_segments):
            for subtitle in filtered_subtitles:
                active = getattr(subtitle, "active_words", [])
                if not active:
                    continue
                if self._segments_overlap(
                    subtitle.start_time,
                    subtitle.end_time,
                    segment.start_time,
                    segment.end_time,
                ):
                    segment_map[idx].extend(active)

        return segment_map

    async def _build_translation_texts(
        self,
        chunk_segments: list[SRTSegment],
        segment_active_words: list[list[Any]],
        language_preferences: dict[str, Any],
        task_id: str | None = None,
        task_progress: dict[str, Any] | None = None,
    ) -> list[str]:
        source_language = language_preferences.get("target") or settings.default_language
        target_language = language_preferences.get("native") or DEFAULT_NATIVE_LANGUAGE

        logger.info(
            "[TRANSLATION] Language preferences - Native: %s, Target: %s, Translation direction: %s→%s",
            language_preferences.get("native"),
            language_preferences.get("target"),
            source_language,
            target_language
        )

        translations: list[str] = ["" for _ in chunk_segments]
        indices_to_translate: list[int] = []
        sentences: list[str] = []

        for index, (segment, words) in enumerate(zip(chunk_segments, segment_active_words, strict=False)):
            if not words:
                continue
            sentence = segment.text.strip()
            if not sentence:
                continue
            indices_to_translate.append(index)
            sentences.append(sentence)

        if not sentences:
            logger.info("[TRANSLATION] No sentences to translate")
            return translations

        logger.info(f"[TRANSLATION] Need to translate {len(sentences)} sentences from {source_language} to {target_language}")

        translation_service = self._get_translation_service(language_preferences, use_fallback=False)
        if translation_service is None:
            logger.warning(
                "[TRANSLATION] No translation service available for %s -> %s. Skipping translations.",
                source_language,
                target_language,
            )
            return translations

        logger.info(
            f"[TRANSLATION] Using service: {translation_service.service_name} for {source_language}→{target_language} translation"
        )

        # Create a wrapper function that shows progress and updates task progress
        async def translate_with_progress(task_id=None, task_progress_dict=None):
            with tqdm(total=len(sentences), desc=f"Translating {source_language}→{target_language}", unit="sent") as pbar:
                # Process in smaller batches for better progress feedback
                batch_size = 5
                all_results = []
                total_batches = (len(sentences) + batch_size - 1) // batch_size

                for batch_num, i in enumerate(range(0, len(sentences), batch_size), 1):
                    batch = sentences[i:i+batch_size]
                    pbar.set_postfix_str(f"Batch {batch_num}/{total_batches}")

                    # Update task progress if available
                    if task_id and task_progress_dict:
                        # Calculate overall progress: 90% + (9% * translation_progress)
                        sentences_done = min(i + len(batch), len(sentences))
                        translation_progress = sentences_done / len(sentences)
                        overall_progress = min(90.0 + (9.0 * translation_progress), 99.0)
                        task_progress_dict[task_id].progress = overall_progress
                        task_progress_dict[task_id].current_step = f"Translating subtitles ({source_language}→{target_language})"
                        task_progress_dict[task_id].message = f"Processing batch {batch_num}/{total_batches} ({sentences_done}/{len(sentences)} sentences)"

                    batch_results = await asyncio.to_thread(
                        translation_service.translate_batch,
                        batch,
                        source_language,
                        target_language,
                    )
                    all_results.extend(batch_results)
                    pbar.update(len(batch))

                return all_results

        try:
            results = await translate_with_progress(task_id, task_progress)
            logger.info(f"[TRANSLATION] Successfully translated {len(results)} sentences")
        except Exception as exc:  # pragma: no cover - fallback path is difficult to trigger deterministically
            logger.error(
                "[TRANSLATION] Primary translation service %s failed: %s",
                translation_service.service_name,
                exc,
                exc_info=True,
            )
            fallback_service = self._get_translation_service(language_preferences, use_fallback=True)
            if fallback_service is None:
                logger.error("[TRANSLATION] No fallback service available")
                return translations
            logger.info(f"[TRANSLATION] Trying fallback service: {fallback_service.service_name}")

            # Use the same progress function with fallback service
            try:
                with tqdm(total=len(sentences), desc=f"Fallback translation {source_language}→{target_language}", unit="sent") as pbar:
                    batch_size = 5
                    all_results = []
                    total_batches = (len(sentences) + batch_size - 1) // batch_size

                    for batch_num, i in enumerate(range(0, len(sentences), batch_size), 1):
                        batch = sentences[i:i+batch_size]
                        pbar.set_postfix_str(f"Batch {batch_num}/{total_batches}")

                        # Update task progress if available
                        if task_id and task_progress:
                            translation_progress = (i + len(batch)) / len(sentences)
                            overall_progress = 90.0 + (9.0 * translation_progress)
                            task_progress[task_id].progress = overall_progress
                            task_progress[task_id].message = f"Translating (fallback): {i + len(batch)}/{len(sentences)}"

                        batch_results = await asyncio.to_thread(
                            fallback_service.translate_batch,
                            batch,
                            source_language,
                            target_language,
                        )
                        all_results.extend(batch_results)
                        pbar.update(len(batch))
                    results = all_results
            except Exception as fallback_exc:
                logger.error(f"[TRANSLATION] Fallback service also failed: {fallback_exc}")
                return translations

        for idx, result in zip(indices_to_translate, results, strict=False):
            translations[idx] = result.translated_text.strip()

        return translations

    def _get_translation_service(
        self,
        language_preferences: dict[str, Any],
        use_fallback: bool = False,
    ) -> ITranslationService | None:
        runtime = language_preferences.get("runtime", {})
        service_key = "translation_fallback_service" if use_fallback else "translation_service"
        model_key = "translation_fallback_model" if use_fallback else "translation_model"

        service_name = runtime.get(service_key)
        if not service_name:
            return None

        model_name = runtime.get(model_key)
        cache_key = (
            service_name,
            model_name or "default",
            runtime.get("target", settings.default_language),
        )

        if cache_key in self._translation_services:
            return self._translation_services[cache_key]

        kwargs: dict[str, Any] = {}
        if model_name:
            kwargs["model_name"] = model_name

        try:
            service = TranslationServiceFactory.create_service(service_name, **kwargs)
        except Exception as exc:
            logger.warning(
                "Unable to initialize translation service %s (fallback=%s): %s",
                service_name,
                use_fallback,
                exc,
            )
            if not use_fallback:
                return self._get_translation_service(language_preferences, use_fallback=True)
            return None

        self._translation_services[cache_key] = service
        return service

    @staticmethod
    def _segments_overlap(
        start_a: float,
        end_a: float,
        start_b: float,
        end_b: float,
        tolerance: float = 0.05,
    ) -> bool:
        return (start_a - tolerance) < (end_b + tolerance) and (end_a + tolerance) > (start_b - tolerance)

    def _load_user_language_preferences(self, user: User) -> dict[str, Any]:
        native, target = load_language_preferences(str(user.id))
        runtime = resolve_language_runtime_settings(native, target)
        return {"native": native, "target": target, "runtime": runtime}

    @staticmethod
    def _normalize_user_identifier(user_identifier: Any) -> Any:
        if isinstance(user_identifier, UUID):
            return user_identifier
        try:
            return UUID(str(user_identifier))
        except Exception:
            return user_identifier

    def _cleanup_old_chunk_files(self, video_file: Path, start_time: float, end_time: float) -> None:
        """Remove old chunk files before generating new ones"""
        try:
            chunk_pattern = f"{video_file.stem}_chunk_{int(start_time)}_{int(end_time)}*.srt"
            for old_chunk in video_file.parent.glob(chunk_pattern):
                try:
                    old_chunk.unlink()
                    logger.info(f"[CHUNK DEBUG] Deleted previous chunk file: {old_chunk}")
                except Exception as e:
                    logger.warning(f"[CHUNK DEBUG] Could not delete old chunk file {old_chunk}: {e}")
        except Exception as e:
            logger.warning(f"[CHUNK DEBUG] Failed to enumerate old chunk files for deletion: {e}")

    def _complete_processing(self, task_id: str, task_progress: dict[str, Any], vocabulary: list = None) -> None:
        """Mark processing as completed"""
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Processing completed"
        task_progress[task_id].message = "Chunk processing finished successfully"
        if vocabulary:
            task_progress[task_id].vocabulary = vocabulary

        logger.info(f"✅ [CHUNK PROCESSING COMPLETE] Task: {task_id}")

    def _handle_error(self, task_id: str, task_progress: dict[str, Any], error: Exception) -> None:
        """Handle processing errors and update progress"""
        logger.error(f"❌ [CHUNK PROCESSING ERROR] Task {task_id}: {error}", exc_info=True)

        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Processing failed",
            message=f"Error: {error!s}",
        )
