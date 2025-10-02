"""
Chunk processing handler service
Extracted from api/routes/processing.py for better separation of concerns
"""

import logging
import time
from pathlib import Path
from typing import Any

from api.models.processing import ProcessingStatus
from services.processing.chunk_processor import ChunkProcessor
from utils.srt_parser import SRTParser

logger = logging.getLogger(__name__)


class ChunkHandler:
    """Handles chunk processing operations for learning content"""

    def __init__(self, chunk_processor: ChunkProcessor = None):
        self.chunk_processor = chunk_processor or ChunkProcessor()

    async def process_chunks(
        self,
        srt_path: str,
        task_id: str,
        task_progress: dict[str, Any],
        user_id: str,
        chunk_size: int = 5,
        overlap: int = 1,
    ) -> dict[str, Any]:
        """
        Process subtitles into learning chunks

        Args:
            srt_path: Path to SRT file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            user_id: User ID for personalized processing
            chunk_size: Number of sentences per chunk
            overlap: Number of overlapping sentences between chunks

        Returns:
            Dictionary containing processed chunks
        """
        try:
            logger.info(f"Starting chunk processing task: {task_id}")

            # Initialize progress tracking
            task_progress[task_id] = ProcessingStatus(
                status="processing",
                progress=0.0,
                current_step="Starting chunk processing...",
                message="Loading subtitle file",
                started_at=int(time.time()),
            )

            # Step 1: Load and parse SRT file
            chunks = await self._load_and_chunk_subtitles(srt_path, task_progress, task_id, chunk_size, overlap)

            # Step 2: Process chunks (20-80% progress)
            processed_chunks = await self._process_chunks(chunks, task_progress, task_id, user_id)

            # Step 3: Format results (80-95% progress)
            formatted_results = await self._format_chunk_results(processed_chunks, task_progress, task_id)

            # Step 4: Save results
            await self._save_chunk_results(formatted_results, srt_path, task_progress, task_id)

            # Mark as complete
            task_progress[task_id].status = "completed"
            task_progress[task_id].progress = 100.0
            task_progress[task_id].message = "Chunk processing completed successfully"
            task_progress[task_id].result = formatted_results
            task_progress[task_id].completed_at = int(time.time())

            logger.info(f"Chunk processing task {task_id} completed successfully")
            return formatted_results

        except Exception as e:
            logger.error(f"Chunk processing task {task_id} failed: {e}")
            task_progress[task_id].status = "failed"
            task_progress[task_id].error = str(e)
            task_progress[task_id].message = f"Chunk processing failed: {e!s}"
            raise

    async def _load_and_chunk_subtitles(
        self, srt_path: str, task_progress: dict[str, Any], task_id: str, chunk_size: int, overlap: int
    ) -> list[dict[str, Any]]:
        """Load and divide subtitles into chunks"""
        task_progress[task_id].progress = 10.0
        task_progress[task_id].current_step = "Loading subtitles..."
        task_progress[task_id].message = "Parsing subtitle file and creating chunks"

        srt_file = Path(srt_path)
        if not srt_file.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")

        # Parse SRT file
        segments = SRTParser.parse_file(str(srt_file))
        if not segments:
            raise ValueError("No subtitle segments found")

        # Create chunks with overlap
        chunks = []
        for i in range(0, len(segments), chunk_size - overlap):
            chunk_segments = segments[i : i + chunk_size]

            chunk = {
                "index": len(chunks),
                "segments": chunk_segments,
                "start_time": chunk_segments[0].start_time,
                "end_time": chunk_segments[-1].end_time,
                "text": " ".join(seg.text for seg in chunk_segments),
            }
            chunks.append(chunk)

            # Stop if we've reached the end
            if i + chunk_size >= len(segments):
                break

        logger.info(f"Created {len(chunks)} chunks from {len(segments)} segments")
        return chunks

    async def _process_chunks(
        self, chunks: list[dict[str, Any]], task_progress: dict[str, Any], task_id: str, user_id: str
    ) -> list[dict[str, Any]]:
        """Process chunks for learning content"""
        task_progress[task_id].progress = 20.0
        task_progress[task_id].current_step = "Processing chunks..."
        task_progress[task_id].message = f"Analyzing {len(chunks)} chunks"

        processed_chunks = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            # Update progress
            progress = 20.0 + (60.0 * i / total_chunks)
            task_progress[task_id].progress = progress
            task_progress[task_id].message = f"Processing chunk {i + 1}/{total_chunks}"

            # Process the chunk
            processed = await self.chunk_processor.process_chunk(chunk, user_id=user_id)
            processed_chunks.append(processed)

        return processed_chunks

    async def _format_chunk_results(
        self, processed_chunks: list[dict[str, Any]], task_progress: dict[str, Any], task_id: str
    ) -> dict[str, Any]:
        """Format processed chunks for output"""
        task_progress[task_id].progress = 85.0
        task_progress[task_id].current_step = "Formatting results..."
        task_progress[task_id].message = "Preparing learning content"

        # Format results
        results = {
            "total_chunks": len(processed_chunks),
            "chunks": processed_chunks,
            "statistics": {
                "average_duration": sum(c.get("end_time", 0) - c.get("start_time", 0) for c in processed_chunks)
                / max(len(processed_chunks), 1),
                "total_duration": sum(c.get("end_time", 0) - c.get("start_time", 0) for c in processed_chunks),
                "vocabulary_count": sum(len(c.get("vocabulary", [])) for c in processed_chunks),
            },
        }

        return results

    async def _save_chunk_results(
        self, results: dict[str, Any], srt_path: str, task_progress: dict[str, Any], task_id: str
    ) -> None:
        """Save chunk processing results to file"""
        task_progress[task_id].progress = 95.0
        task_progress[task_id].current_step = "Saving results..."
        task_progress[task_id].message = "Creating chunk output files"

        # Save chunk data
        import json

        output_path = Path(srt_path).with_suffix(".chunks.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        task_progress[task_id].result_path = str(output_path)
        logger.info(f"Saved chunk results to {output_path}")

    def estimate_duration(self, srt_path: str) -> int:
        """
        Estimate chunk processing duration in seconds

        Args:
            srt_path: Path to SRT file

        Returns:
            Estimated duration in seconds

        Raises:
            Exception: If SRT file cannot be parsed
        """
        segments = SRTParser.parse_file(srt_path)
        # Estimate: 0.3 seconds per segment
        return max(15, len(segments) * 0.3)
