"""
Full processing pipeline handler service
Extracted from api/routes/processing.py for better separation of concerns
"""

import logging
import time
from pathlib import Path
from typing import Any

from api.models.processing import ProcessingStatus
from services.processing.chunk_handler import ChunkHandler
from services.processing.filtering_handler import FilteringHandler
from services.processing.transcription_handler import TranscriptionHandler
from services.processing.translation_handler import TranslationHandler

logger = logging.getLogger(__name__)


class PipelineHandler:
    """Handles full processing pipeline operations"""

    def __init__(
        self,
        transcription_handler: TranscriptionHandler = None,
        filtering_handler: FilteringHandler = None,
        translation_handler: TranslationHandler = None,
        chunk_handler: ChunkHandler = None,
    ):
        self.transcription_handler = transcription_handler
        self.filtering_handler = filtering_handler
        self.translation_handler = translation_handler
        self.chunk_handler = chunk_handler

    async def run_full_pipeline(
        self,
        video_path: str,
        task_id: str,
        task_progress: dict[str, Any],
        user_id: str,
        source_language: str = "de",
        target_language: str = "en",
        user_level: str = "A1",
    ) -> dict[str, Any]:
        """
        Run complete processing pipeline: Transcribe -> Filter -> Translate -> Chunk

        Args:
            video_path: Path to video file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            user_id: User ID for personalized processing
            source_language: Source language for transcription
            target_language: Target language for translation
            user_level: User's language proficiency level

        Returns:
            Dictionary containing pipeline results
        """
        try:
            logger.info(f"Starting full pipeline task: {task_id} for user {user_id}")

            # Initialize progress tracking
            task_progress[task_id] = ProcessingStatus(
                status="processing",
                progress=0.0,
                current_step="Initializing pipeline...",
                message="Preparing to process video",
                started_at=int(time.time()),
            )

            video_file = Path(video_path)
            srt_path = str(video_file.with_suffix(".srt"))
            results = {}

            # Phase 1: Transcription (0-30%)
            if self.transcription_handler:
                logger.info(f"Phase 1: Transcription starting for task {task_id}")
                await self._run_transcription_phase(video_path, srt_path, task_progress, task_id, source_language)
                results["transcription"] = {"srt_path": srt_path}

            # Phase 2: Filtering (30-50%)
            if self.filtering_handler:
                logger.info(f"Phase 2: Filtering starting for task {task_id}")
                filter_results = await self._run_filtering_phase(
                    srt_path, task_progress, task_id, user_id, user_level, source_language
                )
                results["filtering"] = filter_results

            # Phase 3: Translation (50-70%)
            if self.translation_handler:
                logger.info(f"Phase 3: Translation starting for task {task_id}")
                translated_path = await self._run_translation_phase(
                    srt_path, task_progress, task_id, source_language, target_language, user_id
                )
                results["translation"] = {"translated_path": translated_path}

            # Phase 4: Chunking (70-90%)
            if self.chunk_handler:
                logger.info(f"Phase 4: Chunking starting for task {task_id}")
                chunk_results = await self._run_chunking_phase(srt_path, task_progress, task_id, user_id)
                results["chunks"] = chunk_results

            # Phase 5: Finalization (90-100%)
            await self._finalize_pipeline(task_progress, task_id, results)

            logger.info(f"Pipeline task {task_id} completed successfully")
            return results

        except Exception as e:
            logger.error(f"Pipeline task {task_id} failed: {e}")
            task_progress[task_id].status = "failed"
            task_progress[task_id].error = str(e)
            task_progress[task_id].message = f"Pipeline failed: {e!s}"
            raise

    async def _run_transcription_phase(
        self, video_path: str, srt_path: str, task_progress: dict[str, Any], task_id: str, language: str
    ) -> None:
        """Run transcription phase of pipeline"""
        task_progress[task_id].progress = 5.0
        task_progress[task_id].current_step = "Phase 1: Transcription"
        task_progress[task_id].message = "Loading transcription model..."

        # Create a sub-task for transcription
        sub_task_id = f"{task_id}_transcription"
        sub_progress = {}

        await self.transcription_handler.run_transcription(video_path, sub_task_id, sub_progress, language)

        # Update main progress based on sub-task
        task_progress[task_id].progress = 30.0
        task_progress[task_id].message = "Transcription completed"

    async def _run_filtering_phase(
        self, srt_path: str, task_progress: dict[str, Any], task_id: str, user_id: str, user_level: str, language: str
    ) -> dict[str, Any]:
        """Run filtering phase of pipeline"""
        task_progress[task_id].progress = 35.0
        task_progress[task_id].current_step = "Phase 2: Filtering"
        task_progress[task_id].message = "Analyzing vocabulary..."

        # Create a sub-task for filtering
        sub_task_id = f"{task_id}_filtering"
        sub_progress = {}

        results = await self.filtering_handler.filter_subtitles(
            srt_path, sub_task_id, sub_progress, user_id, user_level, language
        )

        # Update main progress
        task_progress[task_id].progress = 50.0
        task_progress[task_id].message = "Filtering completed"

        return results

    async def _run_translation_phase(
        self,
        srt_path: str,
        task_progress: dict[str, Any],
        task_id: str,
        source_language: str,
        target_language: str,
        user_id: str,
    ) -> str:
        """Run translation phase of pipeline"""
        task_progress[task_id].progress = 55.0
        task_progress[task_id].current_step = "Phase 3: Translation"
        task_progress[task_id].message = f"Translating {source_language} to {target_language}..."

        # Create a sub-task for translation
        sub_task_id = f"{task_id}_translation"
        sub_progress = {}

        translated_path = await self.translation_handler.translate_subtitles(
            srt_path, sub_task_id, sub_progress, source_language, target_language, user_id
        )

        # Update main progress
        task_progress[task_id].progress = 70.0
        task_progress[task_id].message = "Translation completed"

        return translated_path

    async def _run_chunking_phase(
        self, srt_path: str, task_progress: dict[str, Any], task_id: str, user_id: str
    ) -> dict[str, Any]:
        """Run chunking phase of pipeline"""
        task_progress[task_id].progress = 75.0
        task_progress[task_id].current_step = "Phase 4: Chunking"
        task_progress[task_id].message = "Creating learning chunks..."

        # Create a sub-task for chunking
        sub_task_id = f"{task_id}_chunking"
        sub_progress = {}

        results = await self.chunk_handler.process_chunks(srt_path, sub_task_id, sub_progress, user_id)

        # Update main progress
        task_progress[task_id].progress = 90.0
        task_progress[task_id].message = "Chunking completed"

        return results

    async def _finalize_pipeline(self, task_progress: dict[str, Any], task_id: str, results: dict[str, Any]) -> None:
        """Finalize pipeline processing"""
        task_progress[task_id].progress = 95.0
        task_progress[task_id].current_step = "Phase 5: Finalization"
        task_progress[task_id].message = "Finalizing results..."

        # Add summary statistics
        results["summary"] = {
            "phases_completed": len(results),
            "total_time": int(time.time()) - task_progress[task_id].started_at,
        }

        # Mark as complete
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].message = "Pipeline completed successfully"
        task_progress[task_id].result = results
        task_progress[task_id].completed_at = int(time.time())

    def estimate_duration(self, video_path: str) -> int:
        """
        Estimate full pipeline duration in seconds

        Args:
            video_path: Path to video file

        Returns:
            Estimated duration in seconds
        """
        # Estimate based on video duration
        # In real implementation, would check actual video duration
        base_estimate = 60  # Base 1 minute

        # Add estimates for each phase
        if self.transcription_handler:
            base_estimate += 60  # Transcription typically takes longer
        if self.filtering_handler:
            base_estimate += 30
        if self.translation_handler:
            base_estimate += 60
        if self.chunk_handler:
            base_estimate += 30

        return base_estimate
