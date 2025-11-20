"""
Parallel Transcription Service

Process audio chunks in parallel for 10x speed improvement.
Uses ThreadPoolExecutor for CPU-based parallelization instead of GPU.

Based on research from fast-audio-video-transcribe (mharrvic).
Research shows: Serial GPU transcription = 10 min for 1-hour content.
Parallel CPU approach = ~1 min for same content (10x improvement).
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from services.parallel_transcription.audio_chunker import AudioChunker, AudioChunkingError

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionChunk:
    """Represents a transcribed audio chunk"""
    index: int
    start_time: float
    end_time: float
    text: str
    segments: List[Any]  # Whisper segments
    confidence: float = 1.0


class ParallelTranscriptionError(Exception):
    """Exception for parallel transcription errors"""
    pass


class ParallelTranscriber:
    """
    Process audio chunks in parallel for faster transcription.

    Architecture:
    - Splits audio into 30s chunks at silence points
    - Processes chunks concurrently (default: 4 workers)
    - Reassembles segments with timestamp adjustment
    - Generates final SRT file

    Performance:
    - 10x faster than serial processing
    - Scales with CPU cores (not GPU-bound)
    - ~1 minute for 1-hour video on 4-core machine

    Example:
        ```python
        transcriber = ParallelTranscriber(
            transcription_service=whisper_service,
            max_workers=4
        )

        result = await transcriber.transcribe_parallel(
            video_path=Path("/videos/video.mp4"),
            progress_callback=lambda p: print(f"Progress: {p}%")
        )

        print(f"Transcribed {len(result.chunks)} chunks")
        print(f"Full text: {result.full_text}")
        print(f"SRT saved to: {result.srt_path}")
        ```
    """

    def __init__(
        self,
        transcription_service: Any,
        max_workers: int = 4,
        chunk_duration: int = 30
    ):
        """
        Initialize parallel transcriber.

        Args:
            transcription_service: Whisper or compatible transcription service
            max_workers: Number of parallel workers (default: 4)
            chunk_duration: Chunk size in seconds (default: 30)
        """
        self.transcription_service = transcription_service
        self.max_workers = max_workers
        self.chunk_duration = chunk_duration
        self.chunker: Optional[AudioChunker] = None

        logger.info(f"ParallelTranscriber initialized with {max_workers} workers")

    def _transcribe_chunk_sync(
        self,
        chunk_path: Path,
        chunk_index: int,
        start_time: float,
        language: str = "de"
    ) -> TranscriptionChunk:
        """
        Transcribe a single chunk (runs in thread pool).

        This method is called in parallel by ThreadPoolExecutor.

        Args:
            chunk_path: Path to audio chunk file
            chunk_index: Chunk number
            start_time: Offset time for this chunk
            language: Target language

        Returns:
            TranscriptionChunk with transcribed text and segments
        """
        try:
            logger.debug(f"Transcribing chunk {chunk_index}: {chunk_path}")

            # Call transcription service (synchronous)
            result = self.transcription_service.transcribe(
                str(chunk_path),
                language=language
            )

            # Extract text and segments
            if hasattr(result, 'full_text'):
                text = result.full_text
                segments = result.segments if hasattr(result, 'segments') else []
            elif isinstance(result, dict):
                text = result.get('text', '')
                segments = result.get('segments', [])
            else:
                text = str(result)
                segments = []

            logger.info(f"Chunk {chunk_index} transcribed: {len(text)} chars, {len(segments)} segments")

            return TranscriptionChunk(
                index=chunk_index,
                start_time=start_time,
                end_time=start_time + self.chunk_duration,  # Approximate
                text=text.strip(),
                segments=segments,
                confidence=1.0
            )

        except Exception as e:
            logger.error(f"Chunk {chunk_index} transcription failed: {e}")
            raise ParallelTranscriptionError(f"Chunk {chunk_index} failed: {e}") from e

    async def transcribe_parallel(
        self,
        video_path: Path,
        language: str = "de",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using parallel chunk processing.

        Steps:
        1. Create intelligent chunks (silence detection)
        2. Extract all chunks
        3. Process chunks in parallel
        4. Reassemble segments with timestamp adjustment
        5. Generate SRT file

        Args:
            video_path: Path to input audio/video file
            language: Target language (default: "de")
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            dict with:
                - full_text: Complete transcription
                - chunks: List of TranscriptionChunk objects
                - segments: All segments with adjusted timestamps
                - srt_path: Path to generated SRT file
                - chunks_processed: Number of chunks

        Raises:
            ParallelTranscriptionError: If transcription fails
        """
        self.chunker = AudioChunker(video_path)

        try:
            # Step 1: Create intelligent chunks (5% progress)
            if progress_callback:
                progress_callback(5)

            chunks = self.chunker.create_intelligent_chunks()
            logger.info(f"Created {len(chunks)} chunks for parallel processing")

            # Step 2: Extract all chunks (5% -> 25% progress)
            if progress_callback:
                progress_callback(10)

            chunk_files = []
            for i, (start, end) in enumerate(chunks):
                chunk_path = await self.chunker.extract_chunk(start, end, i)
                chunk_files.append((chunk_path, i, start))

                if progress_callback:
                    progress = 10 + (i / len(chunks)) * 15
                    progress_callback(progress)

            logger.info(f"Extracted {len(chunk_files)} chunk files")

            # Step 3: Process chunks in parallel (25% -> 90% progress)
            if progress_callback:
                progress_callback(25)

            results = []
            loop = asyncio.get_running_loop()

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all chunk transcriptions
                futures = {
                    executor.submit(
                        self._transcribe_chunk_sync,
                        path,
                        idx,
                        start_time,
                        language
                    ): (idx, start_time)
                    for path, idx, start_time in chunk_files
                }

                # Collect results as they complete
                completed = 0
                for future in as_completed(futures):
                    idx, start_time = futures[future]
                    try:
                        result = future.result()
                        results.append((idx, start_time, result))
                        completed += 1

                        if progress_callback:
                            progress = 25 + (completed / len(chunks)) * 65
                            progress_callback(progress)

                        logger.info(f"Chunk {idx} completed ({completed}/{len(chunks)})")

                    except Exception as e:
                        logger.error(f"Chunk {idx} failed: {e}")
                        raise ParallelTranscriptionError(f"Chunk {idx} processing failed") from e

            # Step 4: Sort by chunk index and reassemble (90% -> 95% progress)
            if progress_callback:
                progress_callback(90)

            results.sort(key=lambda x: x[0])

            full_text = " ".join(r[2].text for r in results)

            # Adjust segment timestamps to match original video
            all_segments = []
            for _, start_time, chunk in results:
                for segment in chunk.segments:
                    # Adjust timestamps by chunk's start time
                    if hasattr(segment, 'start_time'):
                        segment.start_time += start_time
                        segment.end_time += start_time
                    all_segments.append(segment)

            logger.info(f"Reassembled {len(all_segments)} segments")

            # Step 5: Generate SRT file (95% -> 100% progress)
            if progress_callback:
                progress_callback(95)

            srt_path = video_path.with_suffix('.srt')
            self._write_srt(all_segments, srt_path)

            logger.info(f"Parallel transcription complete: {srt_path}")

            if progress_callback:
                progress_callback(100)

            return {
                'full_text': full_text,
                'chunks': [r[2] for r in results],
                'segments': all_segments,
                'srt_path': str(srt_path),
                'chunks_processed': len(results),
            }

        except AudioChunkingError as e:
            logger.error(f"Audio chunking failed: {e}")
            raise ParallelTranscriptionError(f"Chunking failed: {e}") from e
        except Exception as e:
            logger.error(f"Parallel transcription failed: {e}")
            raise ParallelTranscriptionError(f"Transcription failed: {e}") from e
        finally:
            if self.chunker:
                self.chunker.cleanup()

    def _write_srt(self, segments: List[Any], output_path: Path) -> None:
        """
        Write segments to SRT file.

        Args:
            segments: List of transcription segments
            output_path: Path to output SRT file
        """
        try:
            from utils.srt_parser import SRTParser, SRTSegment

            # Convert segments to SRT format
            srt_segments = []
            for i, seg in enumerate(segments, start=1):
                if hasattr(seg, 'start_time') and hasattr(seg, 'end_time') and hasattr(seg, 'text'):
                    srt_segment = SRTSegment(
                        index=i,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        text=seg.text.strip()
                    )
                    srt_segments.append(srt_segment)

            # Write SRT file
            parser = SRTParser()
            srt_content = parser.segments_to_srt(srt_segments)
            output_path.write_text(srt_content, encoding='utf-8')

            logger.info(f"SRT file created: {output_path} ({len(srt_segments)} segments)")

        except Exception as e:
            logger.error(f"Failed to write SRT file: {e}")
            raise ParallelTranscriptionError(f"SRT creation failed: {e}") from e
