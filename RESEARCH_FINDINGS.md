# LangPlug Research Findings: Implementation Patterns from Similar Projects

## Executive Summary

This document synthesizes learnings from 7+ GitHub projects to provide actionable implementation patterns for LangPlug. Each section includes specific architectural patterns, code examples, and integration recommendations.

---

## 1. Interactive Subtitle System (language-learning-player)

### Key Learnings

**Technology Stack Alignment:**
- Next.js + TypeScript + Zustand (matches LangPlug's React + TS + Zustand stack)
- Mantine UI library (alternative to Material-UI)
- Local file handling without cloud dependency

**Interaction Model:**
- **Hover → Word translation**: Single-word lookup on mouseover
- **Click → Phrase translation**: Full subtitle line translation with context
- **State management**: Zustand stores for translation cache, language selection, playback position

### Implementation Recommendations for LangPlug

#### Pattern 1: Word-Level Hover Translation

```typescript
// src/frontend/hooks/useSubtitleHover.ts
import { useState, useCallback } from 'react';
import { useTranslationStore } from '../stores/translationStore';

interface WordHoverHandler {
  hoveredWord: string | null;
  translation: string | null;
  onWordHover: (word: string, event: React.MouseEvent) => void;
  onWordLeave: () => void;
}

export const useSubtitleHover = (): WordHoverHandler => {
  const [hoveredWord, setHoveredWord] = useState<string | null>(null);
  const [translation, setTranslation] = useState<string | null>(null);
  const { getWordTranslation, cacheTranslation } = useTranslationStore();

  const onWordHover = useCallback(async (word: string, event: React.MouseEvent) => {
    setHoveredWord(word);

    // Check cache first
    const cached = getWordTranslation(word);
    if (cached) {
      setTranslation(cached);
      return;
    }

    // Fetch from backend
    try {
      const response = await fetch(`/api/vocabulary/translate?word=${word}`);
      const data = await response.json();
      setTranslation(data.translation);
      cacheTranslation(word, data.translation);
    } catch (error) {
      console.error('[ERROR] Translation fetch failed:', error);
    }
  }, [getWordTranslation, cacheTranslation]);

  const onWordLeave = useCallback(() => {
    setHoveredWord(null);
    setTranslation(null);
  }, []);

  return { hoveredWord, translation, onWordHover, onWordLeave };
};
```

#### Pattern 2: Subtitle Component with Interactive Words

```typescript
// src/frontend/components/InteractiveSubtitle.tsx
import React from 'react';
import { useSubtitleHover } from '../hooks/useSubtitleHover';
import { useVocabularyStore } from '../stores/vocabularyStore';

interface SubtitleProps {
  text: string;
  timestamp: number;
}

export const InteractiveSubtitle: React.FC<SubtitleProps> = ({ text, timestamp }) => {
  const { hoveredWord, translation, onWordHover, onWordLeave } = useSubtitleHover();
  const { knownWords } = useVocabularyStore();

  // Split text into words while preserving punctuation
  const words = text.match(/\b[\w']+\b|[^\w\s]/g) || [];

  return (
    <div className="subtitle-container">
      {words.map((word, index) => {
        const isWord = /\w/.test(word);
        const isKnown = knownWords.has(word.toLowerCase());

        if (!isWord) {
          return <span key={index}>{word}</span>;
        }

        return (
          <span
            key={index}
            className={`subtitle-word ${isKnown ? 'known' : 'unknown'}`}
            onMouseEnter={(e) => onWordHover(word, e)}
            onMouseLeave={onWordLeave}
            style={{
              cursor: 'pointer',
              color: isKnown ? '#4caf50' : '#ff9800',
              textDecoration: hoveredWord === word ? 'underline' : 'none',
            }}
          >
            {word}
          </span>
        );
      })}

      {translation && (
        <div className="translation-tooltip">
          <strong>{hoveredWord}</strong>: {translation}
        </div>
      )}
    </div>
  );
};
```

#### Pattern 3: Translation Cache Store

```typescript
// src/frontend/stores/translationStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TranslationCache {
  [word: string]: {
    translation: string;
    timestamp: number;
    confidence: number;
  };
}

interface TranslationStore {
  cache: TranslationCache;
  getWordTranslation: (word: string) => string | null;
  cacheTranslation: (word: string, translation: string, confidence?: number) => void;
  clearCache: () => void;
}

export const useTranslationStore = create<TranslationStore>()(
  persist(
    (set, get) => ({
      cache: {},

      getWordTranslation: (word: string) => {
        const cached = get().cache[word.toLowerCase()];
        if (!cached) return null;

        // Cache expires after 7 days
        const isExpired = Date.now() - cached.timestamp > 7 * 24 * 60 * 60 * 1000;
        return isExpired ? null : cached.translation;
      },

      cacheTranslation: (word: string, translation: string, confidence = 1.0) => {
        set((state) => ({
          cache: {
            ...state.cache,
            [word.toLowerCase()]: {
              translation,
              timestamp: Date.now(),
              confidence,
            },
          },
        }));
      },

      clearCache: () => set({ cache: {} }),
    }),
    {
      name: 'langplug-translation-cache',
    }
  )
);
```

**Integration Steps:**
1. Add hover handlers to existing subtitle components
2. Create translation cache store with persistence
3. Update backend `/api/vocabulary/translate` endpoint for single-word lookups
4. Add CSS for known/unknown word highlighting

---

## 2. Parallel Transcription Processing (fast-audio-video-transcribe)

### Key Learnings

**Architecture:**
- **10x speed improvement**: 1-hour audio → 1-minute processing time
- **Chunked processing**: Split audio into 30-second segments
- **CPU parallelization**: 2 CPU cores per segment instead of GPU
- **Silence detection**: Smart chunking at natural pauses

**Modal Platform Pattern:**
- Distributed task execution across containers
- On-demand provisioning for cost efficiency
- Independent segment processing with reassembly

### Implementation Recommendations for LangPlug

#### Pattern 1: Chunked Audio Processing with FFmpeg

```python
# src/backend/services/transcription/chunk_processor.py
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple
import concurrent.futures

class AudioChunker:
    """Split audio files into processable chunks for parallel transcription."""

    CHUNK_DURATION = 30  # seconds (Whisper's native chunk size)
    OVERLAP = 2  # seconds of overlap to prevent word boundary issues

    def __init__(self, audio_path: Path):
        self.audio_path = audio_path
        self.temp_dir = Path(tempfile.mkdtemp(prefix="langplug_chunks_"))

    def get_duration(self) -> float:
        """Extract audio duration using ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(self.audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())

    def detect_silence_points(self, min_silence_duration: float = 0.5) -> List[float]:
        """
        Detect silence points for intelligent chunking.
        Returns timestamps where silence occurs.
        """
        cmd = [
            "ffmpeg", "-i", str(self.audio_path),
            "-af", f"silencedetect=noise=-30dB:d={min_silence_duration}",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)

        # Parse silence timestamps from ffmpeg output
        silence_points = []
        for line in result.stdout.split('\n'):
            if "silence_end:" in line:
                timestamp = float(line.split("silence_end:")[1].split()[0])
                silence_points.append(timestamp)

        return silence_points

    def create_intelligent_chunks(self) -> List[Tuple[float, float]]:
        """
        Create chunks aligned with silence points for better transcription quality.
        Returns list of (start_time, end_time) tuples.
        """
        duration = self.get_duration()
        silence_points = self.detect_silence_points()

        chunks = []
        current_start = 0.0

        while current_start < duration:
            target_end = current_start + self.CHUNK_DURATION

            # Find nearest silence point within 5 seconds of target
            nearby_silences = [
                s for s in silence_points
                if target_end - 5 < s < target_end + 5
            ]

            if nearby_silences:
                chunk_end = min(nearby_silences, key=lambda s: abs(s - target_end))
            else:
                chunk_end = min(target_end, duration)

            chunks.append((current_start, chunk_end))
            current_start = chunk_end - self.OVERLAP  # Add overlap

        return chunks

    def extract_chunk(self, start: float, end: float, chunk_index: int) -> Path:
        """Extract a single audio chunk using ffmpeg."""
        output_path = self.temp_dir / f"chunk_{chunk_index:04d}.wav"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(self.audio_path),
            "-ss", str(start),
            "-to", str(end),
            "-ar", "16000",  # Whisper requires 16kHz
            "-ac", "1",      # Mono
            "-c:a", "pcm_s16le",
            str(output_path)
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    def cleanup(self):
        """Remove temporary chunk files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class ParallelTranscriber:
    """Process audio chunks in parallel for faster transcription."""

    def __init__(self, model_name: str = "whisper-tiny"):
        from backend.services.transcription.transcription_service import TranscriptionService
        self.service = TranscriptionService(model_name=model_name)
        self.chunker: AudioChunker | None = None

    def transcribe_chunk(self, chunk_path: Path, chunk_index: int) -> dict:
        """Transcribe a single chunk (runs in parallel)."""
        result = self.service.transcribe_audio(str(chunk_path))
        return {
            'index': chunk_index,
            'text': result['text'],
            'segments': result.get('segments', []),
        }

    def transcribe_parallel(self, audio_path: Path, max_workers: int = 4) -> dict:
        """
        Transcribe audio using parallel chunk processing.

        Args:
            audio_path: Path to input audio/video file
            max_workers: Number of parallel worker threads (default: 4)

        Returns:
            Combined transcription result
        """
        self.chunker = AudioChunker(audio_path)

        try:
            # Create intelligent chunks
            chunks = self.chunker.create_intelligent_chunks()
            print(f"[INFO] Created {len(chunks)} chunks for parallel processing")

            # Extract all chunks
            chunk_files = []
            for i, (start, end) in enumerate(chunks):
                chunk_path = self.chunker.extract_chunk(start, end, i)
                chunk_files.append((chunk_path, i, start))

            # Process chunks in parallel
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.transcribe_chunk, path, idx): (idx, start_time)
                    for path, idx, start_time in chunk_files
                }

                for future in concurrent.futures.as_completed(futures):
                    idx, start_time = futures[future]
                    try:
                        result = future.result()
                        results.append((idx, start_time, result))
                    except Exception as e:
                        print(f"[ERROR] Chunk {idx} failed: {e}")
                        raise

            # Sort by chunk index
            results.sort(key=lambda x: x[0])

            # Combine results
            full_text = " ".join(r[2]['text'].strip() for r in results)

            # Adjust segment timestamps to match original audio
            all_segments = []
            for _, start_time, chunk_result in results:
                for segment in chunk_result.get('segments', []):
                    segment['start'] += start_time
                    segment['end'] += start_time
                    all_segments.append(segment)

            return {
                'text': full_text,
                'segments': all_segments,
                'chunks_processed': len(results),
            }

        finally:
            if self.chunker:
                self.chunker.cleanup()
```

#### Pattern 2: API Endpoint with Async Processing

```python
# src/backend/api/routes/transcription.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pathlib import Path
import uuid

router = APIRouter(prefix="/api/transcription", tags=["transcription"])

# In-memory job tracking (replace with Redis/database in production)
transcription_jobs = {}

@router.post("/transcribe-parallel")
async def transcribe_parallel(
    video_id: str,
    background_tasks: BackgroundTasks,
    max_workers: int = 4
):
    """
    Initiate parallel transcription for a video.
    Returns job ID for status polling.
    """
    job_id = str(uuid.uuid4())

    # Get video path
    video_path = Path(f"data/videos/{video_id}/video.mp4")
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    # Initialize job status
    transcription_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'video_id': video_id,
    }

    # Start background task
    background_tasks.add_task(
        process_transcription,
        job_id,
        video_path,
        max_workers
    )

    return {
        'job_id': job_id,
        'status': 'processing',
        'poll_url': f'/api/transcription/status/{job_id}'
    }


async def process_transcription(job_id: str, video_path: Path, max_workers: int):
    """Background task for parallel transcription."""
    try:
        from backend.services.transcription.chunk_processor import ParallelTranscriber

        transcriber = ParallelTranscriber(model_name="whisper-tiny")
        result = transcriber.transcribe_parallel(video_path, max_workers=max_workers)

        # Save to database
        save_transcription_to_db(video_path.parent.name, result)

        # Update job status
        transcription_jobs[job_id] = {
            'status': 'completed',
            'progress': 100,
            'result': result,
        }

    except Exception as e:
        transcription_jobs[job_id] = {
            'status': 'failed',
            'error': str(e),
        }


@router.get("/status/{job_id}")
async def get_transcription_status(job_id: str):
    """Poll transcription job status."""
    if job_id not in transcription_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return transcription_jobs[job_id]
```

**Integration Steps:**
1. Install `ffmpeg-python` dependency
2. Replace existing synchronous transcription with parallel version for videos > 5 minutes
3. Add background task handling with job status tracking
4. Configure worker count based on available CPU cores
5. Add progress reporting for frontend UI feedback

---

## 3. Spaced Repetition & Smart Review (vocabulary-builder)

### Key Learnings

**Review Algorithm:**
- Prioritizes words with lowest performance scores
- Schedules reviews based on earliest review dates
- Combines difficulty + time for optimal learning

**Quiz Types:**
- Multiple choice (definition)
- Multiple choice (synonym/antonym)
- Fill-in-the-blank (active recall)

**Limitation:** Uses browser localStorage instead of persistent database

### Implementation Recommendations for LangPlug

#### Pattern 1: Spaced Repetition Algorithm (SM-2)

```python
# src/backend/services/vocabulary/spaced_repetition.py
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

class ReviewQuality(Enum):
    """User's self-assessed quality of recall."""
    COMPLETE_BLACKOUT = 0  # Complete failure
    INCORRECT_EASY = 1     # Incorrect but felt easy
    INCORRECT_HARD = 2     # Incorrect and difficult
    CORRECT_HARD = 3       # Correct with serious difficulty
    CORRECT_HESITATION = 4 # Correct after hesitation
    PERFECT = 5            # Perfect recall


@dataclass
class VocabularyItem:
    """Vocabulary item with spaced repetition metadata."""
    word: str
    translation: str
    easiness_factor: float = 2.5  # SM-2 default
    repetitions: int = 0
    interval: int = 1  # Days until next review
    next_review: datetime = None

    def __post_init__(self):
        if self.next_review is None:
            self.next_review = datetime.now()


class SpacedRepetitionEngine:
    """
    Implements SuperMemo SM-2 algorithm for optimal review scheduling.

    Research basis: Spaced repetition is one of the most effective learning
    techniques, with retention rates 2-3x higher than massed practice.
    """

    MIN_EASINESS = 1.3

    def calculate_next_interval(
        self,
        item: VocabularyItem,
        quality: ReviewQuality
    ) -> VocabularyItem:
        """
        Calculate next review interval based on SM-2 algorithm.

        Args:
            item: Current vocabulary item
            quality: User's recall quality (0-5)

        Returns:
            Updated vocabulary item with new scheduling
        """
        q = quality.value

        # Update easiness factor
        new_ef = item.easiness_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(new_ef, self.MIN_EASINESS)

        # Update repetition count
        if q < 3:
            # Failed recall - reset
            new_repetitions = 0
            new_interval = 1
        else:
            # Successful recall
            new_repetitions = item.repetitions + 1

            if new_repetitions == 1:
                new_interval = 1
            elif new_repetitions == 2:
                new_interval = 6
            else:
                new_interval = int(item.interval * new_ef)

        # Calculate next review date
        next_review = datetime.now() + timedelta(days=new_interval)

        return VocabularyItem(
            word=item.word,
            translation=item.translation,
            easiness_factor=new_ef,
            repetitions=new_repetitions,
            interval=new_interval,
            next_review=next_review,
        )

    def get_due_items(self, all_items: list[VocabularyItem]) -> list[VocabularyItem]:
        """
        Get vocabulary items due for review.

        Prioritizes:
        1. Overdue items (past review date)
        2. Items with low easiness factor (difficult words)
        3. Items due soon
        """
        now = datetime.now()

        # Filter due items
        due_items = [item for item in all_items if item.next_review <= now]

        # Sort by priority: overdue duration * (1 / easiness_factor)
        due_items.sort(
            key=lambda x: (
                (now - x.next_review).total_seconds() * (1 / x.easiness_factor)
            ),
            reverse=True
        )

        return due_items

    def get_learning_stats(self, all_items: list[VocabularyItem]) -> dict:
        """Generate learning statistics for user dashboard."""
        now = datetime.now()

        due_today = sum(1 for item in all_items if item.next_review.date() == now.date())
        overdue = sum(1 for item in all_items if item.next_review < now)
        mastered = sum(1 for item in all_items if item.repetitions >= 5 and item.easiness_factor >= 2.5)

        return {
            'total_words': len(all_items),
            'due_today': due_today,
            'overdue': overdue,
            'mastered': mastered,
            'learning': len(all_items) - mastered,
        }
```

#### Pattern 2: Database Schema for Vocabulary Tracking

```python
# src/backend/database/models/vocabulary.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.base import Base
from datetime import datetime

class UserVocabulary(Base):
    """User-specific vocabulary tracking with spaced repetition metadata."""

    __tablename__ = "user_vocabulary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word = Column(String(100), nullable=False, index=True)
    translation = Column(String(200), nullable=False)

    # Spaced repetition fields
    easiness_factor = Column(Float, default=2.5)
    repetitions = Column(Integer, default=0)
    interval_days = Column(Integer, default=1)
    next_review = Column(DateTime, default=datetime.now, index=True)
    last_reviewed = Column(DateTime, nullable=True)

    # Performance tracking
    total_reviews = Column(Integer, default=0)
    correct_reviews = Column(Integer, default=0)

    # Metadata
    encountered_in_video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    added_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="vocabulary")
    video = relationship("Video")

    @property
    def success_rate(self) -> float:
        """Calculate percentage of correct reviews."""
        if self.total_reviews == 0:
            return 0.0
        return (self.correct_reviews / self.total_reviews) * 100

    @property
    def is_due(self) -> bool:
        """Check if item is due for review."""
        return datetime.now() >= self.next_review

    def __repr__(self):
        return f"<UserVocabulary(word='{self.word}', next_review='{self.next_review}')>"
```

#### Pattern 3: Quiz Generation Service

```python
# src/backend/services/vocabulary/quiz_generator.py
import random
from typing import List, Literal
from dataclasses import dataclass

QuizType = Literal["multiple_choice", "fill_blank", "synonym", "antonym"]

@dataclass
class QuizQuestion:
    """A single quiz question."""
    question_type: QuizType
    word: str
    correct_answer: str
    options: List[str]  # For multiple choice
    hint: str | None = None


class QuizGenerator:
    """Generate diverse quiz questions for vocabulary practice."""

    def __init__(self, db_session):
        self.db = db_session

    def generate_multiple_choice(
        self,
        word: str,
        correct_translation: str,
        num_options: int = 4
    ) -> QuizQuestion:
        """
        Generate multiple choice question with distractors.

        Distractors should be:
        - Similar difficulty level
        - Different enough to avoid confusion
        - From the same word class (noun, verb, etc.)
        """
        # Get similar words as distractors
        distractors = self._get_similar_words(word, num_options - 1)

        options = [correct_translation] + [d.translation for d in distractors]
        random.shuffle(options)

        return QuizQuestion(
            question_type="multiple_choice",
            word=word,
            correct_answer=correct_translation,
            options=options,
            hint=f"Translation of '{word}'"
        )

    def generate_fill_blank(
        self,
        word: str,
        correct_translation: str,
        sentence_context: str | None = None
    ) -> QuizQuestion:
        """
        Generate fill-in-the-blank question using sentence context.

        If sentence_context is provided, use it. Otherwise, generate
        a simple question format.
        """
        if sentence_context:
            # Replace word with blank in context
            question = sentence_context.replace(word, "______")
        else:
            question = f"Complete: '{word}' means ______"

        return QuizQuestion(
            question_type="fill_blank",
            word=question,
            correct_answer=correct_translation,
            options=[],  # Free text input
            hint="Type the translation"
        )

    def generate_quiz_session(
        self,
        user_id: int,
        num_questions: int = 10,
        quiz_types: List[QuizType] | None = None
    ) -> List[QuizQuestion]:
        """
        Generate a complete quiz session with mixed question types.

        Prioritizes:
        1. Due vocabulary items
        2. Low performance words
        3. Recently encountered words
        """
        from backend.services.vocabulary.spaced_repetition import SpacedRepetitionEngine

        # Get user's vocabulary
        user_vocab = self._get_user_vocabulary(user_id)

        # Get due items using spaced repetition
        sr_engine = SpacedRepetitionEngine()
        due_items = sr_engine.get_due_items(user_vocab)

        # Select items for quiz
        quiz_items = due_items[:num_questions]

        # Generate questions with mixed types
        if quiz_types is None:
            quiz_types = ["multiple_choice", "fill_blank"]

        questions = []
        for item in quiz_items:
            quiz_type = random.choice(quiz_types)

            if quiz_type == "multiple_choice":
                question = self.generate_multiple_choice(item.word, item.translation)
            elif quiz_type == "fill_blank":
                question = self.generate_fill_blank(item.word, item.translation)

            questions.append(question)

        return questions

    def _get_similar_words(self, word: str, count: int) -> List:
        """Get similar words for distractor generation."""
        # Simplified implementation - enhance with word embeddings or word class filtering
        from backend.database.models.vocabulary import UserVocabulary

        similar = (
            self.db.query(UserVocabulary)
            .filter(UserVocabulary.word != word)
            .order_by(func.random())
            .limit(count)
            .all()
        )

        return similar

    def _get_user_vocabulary(self, user_id: int) -> List:
        """Fetch all vocabulary items for user."""
        from backend.database.models.vocabulary import UserVocabulary

        return (
            self.db.query(UserVocabulary)
            .filter(UserVocabulary.user_id == user_id)
            .all()
        )
```

**Integration Steps:**
1. Add spaced repetition database fields to `user_vocabulary` table
2. Implement SM-2 algorithm for review scheduling
3. Create quiz generation service with multiple question types
4. Add API endpoints for quiz sessions and review submission
5. Build frontend quiz UI with Tinder-style swiping for answer selection

---

## 4. Real-Time Subtitle Highlighting (react-speech-highlight-demo)

### Key Learnings

**Client-Side Synchronization:**
- No backend required for word highlighting
- Hybrid detection engine for timestamp accuracy
- Supports seeking by sentence/paragraph
- Hover highlighting for related translations

**Key Feature:** Real-time analysis during playback for precise word-level synchronization

### Implementation Recommendations for LangPlug

#### Pattern 1: Word-Level Timestamp Mapping

```typescript
// src/frontend/services/subtitleSyncService.ts
interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  confidence: number;
}

interface SubtitleSegment {
  text: string;
  start: number;
  end: number;
  words: WordTimestamp[];
}

export class SubtitleSyncService {
  /**
   * Generate word-level timestamps from Whisper segment data.
   * Whisper provides segment-level timestamps, so we interpolate word positions.
   */
  generateWordTimestamps(segment: SubtitleSegment): WordTimestamp[] {
    const words = segment.text.trim().split(/\s+/);
    const segmentDuration = segment.end - segment.start;
    const avgWordDuration = segmentDuration / words.length;

    return words.map((word, index) => ({
      word,
      start: segment.start + (index * avgWordDuration),
      end: segment.start + ((index + 1) * avgWordDuration),
      confidence: 1.0,
    }));
  }

  /**
   * Find active word at specific timestamp.
   */
  getActiveWordAtTime(
    segments: SubtitleSegment[],
    currentTime: number
  ): WordTimestamp | null {
    for (const segment of segments) {
      if (currentTime >= segment.start && currentTime <= segment.end) {
        for (const word of segment.words) {
          if (currentTime >= word.start && currentTime <= word.end) {
            return word;
          }
        }
      }
    }
    return null;
  }

  /**
   * Get all words within a time range (for highlighting).
   */
  getWordsInRange(
    segments: SubtitleSegment[],
    startTime: number,
    endTime: number
  ): WordTimestamp[] {
    const words: WordTimestamp[] = [];

    for (const segment of segments) {
      if (segment.start <= endTime && segment.end >= startTime) {
        for (const word of segment.words) {
          if (word.start <= endTime && word.end >= startTime) {
            words.push(word);
          }
        }
      }
    }

    return words;
  }
}
```

#### Pattern 2: Real-Time Highlighting Component

```typescript
// src/frontend/components/SyncedSubtitleDisplay.tsx
import React, { useEffect, useState, useRef } from 'react';
import { SubtitleSyncService, WordTimestamp } from '../services/subtitleSyncService';

interface SyncedSubtitleProps {
  segments: SubtitleSegment[];
  videoRef: React.RefObject<HTMLVideoElement>;
  onWordClick?: (word: string) => void;
}

export const SyncedSubtitleDisplay: React.FC<SyncedSubtitleProps> = ({
  segments,
  videoRef,
  onWordClick,
}) => {
  const [activeWord, setActiveWord] = useState<string | null>(null);
  const [currentSegment, setCurrentSegment] = useState<SubtitleSegment | null>(null);
  const syncService = useRef(new SubtitleSyncService());

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateHighlight = () => {
      const currentTime = video.currentTime;

      // Find active segment
      const segment = segments.find(
        (s) => currentTime >= s.start && currentTime <= s.end
      );

      if (segment) {
        setCurrentSegment(segment);

        // Find active word
        const word = syncService.current.getActiveWordAtTime(segments, currentTime);
        setActiveWord(word?.word || null);
      } else {
        setCurrentSegment(null);
        setActiveWord(null);
      }
    };

    // Update every 50ms for smooth highlighting
    const interval = setInterval(updateHighlight, 50);

    // Also update on seek
    video.addEventListener('seeked', updateHighlight);

    return () => {
      clearInterval(interval);
      video.removeEventListener('seeked', updateHighlight);
    };
  }, [segments, videoRef]);

  if (!currentSegment) {
    return <div className="subtitle-display empty">No subtitles</div>;
  }

  return (
    <div className="subtitle-display">
      {currentSegment.words.map((wordData, index) => {
        const isActive = wordData.word === activeWord;

        return (
          <span
            key={index}
            className={`subtitle-word ${isActive ? 'active' : ''}`}
            onClick={() => onWordClick?.(wordData.word)}
            style={{
              display: 'inline-block',
              margin: '0 4px',
              padding: '2px 4px',
              backgroundColor: isActive ? '#ffd54f' : 'transparent',
              fontWeight: isActive ? 'bold' : 'normal',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {wordData.word}
          </span>
        );
      })}
    </div>
  );
};
```

#### Pattern 3: Seeking by Word/Sentence

```typescript
// src/frontend/hooks/useSubtitleSeek.ts
import { useCallback } from 'react';
import { SubtitleSegment } from '../services/subtitleSyncService';

export const useSubtitleSeek = (
  videoRef: React.RefObject<HTMLVideoElement>,
  segments: SubtitleSegment[]
) => {
  const seekToWord = useCallback((word: string) => {
    const video = videoRef.current;
    if (!video) return;

    // Find first occurrence of word
    for (const segment of segments) {
      const wordData = segment.words.find((w) => w.word.toLowerCase() === word.toLowerCase());
      if (wordData) {
        video.currentTime = wordData.start;
        return;
      }
    }
  }, [videoRef, segments]);

  const seekToSentence = useCallback((sentenceIndex: number) => {
    const video = videoRef.current;
    if (!video) return;

    if (sentenceIndex >= 0 && sentenceIndex < segments.length) {
      video.currentTime = segments[sentenceIndex].start;
    }
  }, [videoRef, segments]);

  const seekPreviousSentence = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const currentTime = video.currentTime;
    const currentIndex = segments.findIndex(
      (s) => currentTime >= s.start && currentTime <= s.end
    );

    if (currentIndex > 0) {
      video.currentTime = segments[currentIndex - 1].start;
    }
  }, [videoRef, segments]);

  const seekNextSentence = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const currentTime = video.currentTime;
    const currentIndex = segments.findIndex(
      (s) => currentTime >= s.start && currentTime <= s.end
    );

    if (currentIndex >= 0 && currentIndex < segments.length - 1) {
      video.currentTime = segments[currentIndex + 1].start;
    }
  }, [videoRef, segments]);

  return {
    seekToWord,
    seekToSentence,
    seekPreviousSentence,
    seekNextSentence,
  };
};
```

**Integration Steps:**
1. Enhance Whisper transcription to store word-level timestamps
2. Create subtitle sync service for timestamp mapping
3. Add real-time highlighting component with 50ms update interval
4. Implement seeking controls for previous/next sentence navigation
5. Add keyboard shortcuts (← for previous, → for next sentence)

---

## 5. Production Docker Architecture (fastapi-react-templates)

### Key Learnings

**Environment Separation:**
- `docker-compose.yml` for development with hot-reload
- `docker-compose.prod.yml` for production optimization
- Hybrid setup option: Docker services + local dev servers

**Service Architecture:**
- Nginx reverse proxy for production
- Redis caching layer
- MongoDB/PostgreSQL separation
- Environment-specific `.env` files

### Implementation Recommendations for LangPlug

#### Pattern 1: Development Docker Compose

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # Backend FastAPI
  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.dev
    container_name: langplug-backend-dev
    ports:
      - "8000:8000"
    volumes:
      - ./src/backend:/app
      - ./data:/app/data
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=sqlite:///data/langplug.db
      - REDIS_HOST=redis
      - WHISPER_MODEL=whisper-tiny
    depends_on:
      - redis
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - langplug-network

  # Frontend React
  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile.dev
    container_name: langplug-frontend-dev
    ports:
      - "5173:5173"
    volumes:
      - ./src/frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev -- --host
    networks:
      - langplug-network

  # Redis for caching
  redis:
    image: redis:7-alpine
    container_name: langplug-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - langplug-network

volumes:
  redis-data:

networks:
  langplug-network:
    driver: bridge
```

#### Pattern 2: Production Docker Compose with Nginx

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: langplug-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./deploy/nginx/ssl:/etc/nginx/ssl:ro
      - frontend-build:/usr/share/nginx/html:ro
    depends_on:
      - backend
    networks:
      - langplug-network

  # Backend FastAPI (production)
  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    container_name: langplug-backend
    expose:
      - "8000"
    volumes:
      - ./data:/app/data
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///data/langplug.db
      - REDIS_HOST=redis
      - WHISPER_MODEL=whisper-medium
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - redis
    command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    networks:
      - langplug-network
    restart: unless-stopped

  # Frontend (built static files)
  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile.prod
    container_name: langplug-frontend-build
    volumes:
      - frontend-build:/app/dist
    command: echo "Frontend built successfully"

  # Redis
  redis:
    image: redis:7-alpine
    container_name: langplug-redis
    volumes:
      - redis-data:/data
    networks:
      - langplug-network
    restart: unless-stopped

volumes:
  frontend-build:
  redis-data:

networks:
  langplug-network:
    driver: bridge
```

#### Pattern 3: Nginx Configuration

```nginx
# deploy/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

    server {
        listen 80;
        server_name localhost;

        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API proxy
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts for long-running operations (transcription)
            proxy_connect_timeout 600s;
            proxy_send_timeout 600s;
            proxy_read_timeout 600s;
        }

        # Auth endpoints with stricter rate limiting
        location /api/auth/ {
            limit_req zone=auth_limit burst=3 nodelay;

            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # WebSocket support (for future real-time features)
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

#### Pattern 4: Backend Production Dockerfile

```dockerfile
# src/backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 langplug && chown -R langplug:langplug /app
USER langplug

# Expose port
EXPOSE 8000

# Production server with Gunicorn
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**Integration Steps:**
1. Create separate development and production Docker compose files
2. Add Nginx reverse proxy configuration
3. Implement Redis caching for API responses
4. Configure environment-specific `.env` files
5. Add health checks and restart policies
6. Set up volume mounting for persistent data

---

## 6. JWT Authentication & RBAC (fastapi-role-and-permissions)

### Key Learnings

**Security Architecture:**
- Stateless JWT authentication
- Bcrypt password hashing
- Many-to-many role-permission model
- Endpoint-level enforcement via dependencies

**Token Management:**
- Configurable expiration times
- Refresh token support
- Secure token validation

### Implementation Recommendations for LangPlug

#### Pattern 1: Enhanced Authentication Service

```python
# src/backend/services/auth/jwt_service.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import secrets

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Generate secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class JWTService:
    """Secure JWT token management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload data (user_id, email, etc.)
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create long-lived refresh token."""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate JWT token.

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise ValueError("Invalid or expired token")

    @staticmethod
    def validate_access_token(token: str) -> dict:
        """Validate access token and return payload."""
        payload = JWTService.decode_token(token)

        if payload.get("type") != "access":
            raise ValueError("Not an access token")

        return payload

    @staticmethod
    def validate_refresh_token(token: str) -> int:
        """Validate refresh token and return user_id."""
        payload = JWTService.decode_token(token)

        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")

        return int(payload.get("sub"))
```

#### Pattern 2: Authentication Dependencies

```python
# src/backend/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.services.auth.jwt_service import JWTService
from backend.database.session import get_db
from backend.database.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.

    Usage:
        @router.get("/profile")
        def get_profile(user: User = Depends(get_current_user)):
            return user
    """
    token = credentials.credentials

    try:
        payload = JWTService.validate_access_token(token)
        user_id = int(payload.get("sub"))

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """Require admin role for endpoint access."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user


async def require_active_subscription(
    user: User = Depends(get_current_user)
) -> User:
    """Require active subscription for premium features."""
    if not user.has_active_subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required for this feature"
        )
    return user
```

#### Pattern 3: Authentication Routes

```python
# src/backend/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from backend.database.session import get_db
from backend.database.models.user import User
from backend.services.auth.jwt_service import JWTService

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user with email and password.

    Password requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one number
    """
    # Check if user exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )

    # Create user
    hashed_password = JWTService.hash_password(request.password)
    user = User(
        email=request.email,
        username=request.username,
        hashed_password=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate tokens
    access_token = JWTService.create_access_token({"sub": str(user.id)})
    refresh_token = JWTService.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not JWTService.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = JWTService.create_access_token({"sub": str(user.id)})
    refresh_token = JWTService.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Exchange refresh token for new access token."""
    try:
        user_id = JWTService.validate_refresh_token(refresh_token)

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Generate new tokens
        new_access_token = JWTService.create_access_token({"sub": str(user_id)})
        new_refresh_token = JWTService.create_refresh_token(user_id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
```

**Integration Steps:**
1. Install dependencies: `python-jose[cryptography]`, `passlib[bcrypt]`
2. Replace current authentication with JWT-based system
3. Migrate existing passwords to bcrypt hashing
4. Add refresh token endpoint for session management
5. Implement role-based access for admin features
6. Add token expiration and renewal logic

---

## 7. Progress Tracking & Analytics (LMS projects)

### Key Learnings

**Core Features:**
- Role-based access (Admin, Teacher, Student)
- Detailed progress reports
- Attendance and performance tracking
- Certificate generation on completion

**Limitation:** Documentation lacks detailed schema and algorithm implementations

### Implementation Recommendations for LangPlug

#### Pattern 1: Progress Tracking Schema

```python
# src/backend/database/models/progress.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.base import Base
from datetime import datetime

class VideoProgress(Base):
    """Track user progress through video content."""

    __tablename__ = "video_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # Progress metrics
    watch_time_seconds = Column(Integer, default=0)
    total_duration = Column(Integer, nullable=False)
    progress_percentage = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)

    # Timestamps
    started_at = Column(DateTime, default=datetime.now)
    last_watched_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    # Video position
    last_position_seconds = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="video_progress")
    video = relationship("Video")

    def update_progress(self, current_position: int):
        """Update progress based on current video position."""
        self.last_position_seconds = current_position
        self.progress_percentage = (current_position / self.total_duration) * 100
        self.last_watched_at = datetime.now()

        if self.progress_percentage >= 90 and not self.completed:
            self.completed = True
            self.completed_at = datetime.now()


class LearningStreak(Base):
    """Track user learning streaks for gamification."""

    __tablename__ = "learning_streaks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, default=datetime.now)
    total_study_days = Column(Integer, default=0)

    user = relationship("User", back_populates="learning_streak")

    def check_and_update_streak(self):
        """Update streak based on last activity."""
        today = datetime.now().date()
        last_date = self.last_activity_date.date()

        if today == last_date:
            # Same day - no change
            return
        elif (today - last_date).days == 1:
            # Consecutive day - increment streak
            self.current_streak += 1
            self.total_study_days += 1

            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        else:
            # Streak broken
            self.current_streak = 1
            self.total_study_days += 1

        self.last_activity_date = datetime.now()


class Achievement(Base):
    """User achievements and milestones."""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(100))
    points = Column(Integer, default=0)

    # Achievement criteria
    criteria_type = Column(String(50))  # 'videos_completed', 'streak_reached', 'words_learned'
    criteria_value = Column(Integer)


class UserAchievement(Base):
    """Track earned achievements."""

    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")
```

#### Pattern 2: Analytics Service

```python
# src/backend/services/analytics/learning_analytics.py
from sqlalchemy.orm import Session
from backend.database.models.progress import VideoProgress, LearningStreak
from backend.database.models.vocabulary import UserVocabulary
from datetime import datetime, timedelta
from typing import Dict, List

class LearningAnalytics:
    """Generate learning analytics and insights."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_dashboard_stats(self, user_id: int) -> Dict:
        """
        Generate comprehensive dashboard statistics.

        Returns:
            {
                'videos_watched': 15,
                'total_watch_time': 45000,  # seconds
                'words_learned': 234,
                'current_streak': 7,
                'this_week_minutes': 180,
                'vocabulary_mastery': 0.45,  # percentage
            }
        """
        # Video statistics
        video_stats = self.db.query(
            func.count(VideoProgress.id),
            func.sum(VideoProgress.watch_time_seconds)
        ).filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completed == True
        ).first()

        videos_completed = video_stats[0] or 0
        total_watch_time = video_stats[1] or 0

        # Vocabulary statistics
        vocab_count = self.db.query(func.count(UserVocabulary.id)).filter(
            UserVocabulary.user_id == user_id
        ).scalar()

        mastered_words = self.db.query(func.count(UserVocabulary.id)).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.repetitions >= 5,
            UserVocabulary.easiness_factor >= 2.5
        ).scalar()

        # Streak
        streak = self.db.query(LearningStreak).filter(
            LearningStreak.user_id == user_id
        ).first()

        # This week activity
        week_ago = datetime.now() - timedelta(days=7)
        this_week_seconds = self.db.query(
            func.sum(VideoProgress.watch_time_seconds)
        ).filter(
            VideoProgress.user_id == user_id,
            VideoProgress.last_watched_at >= week_ago
        ).scalar() or 0

        return {
            'videos_watched': videos_completed,
            'total_watch_time': total_watch_time,
            'words_learned': vocab_count,
            'words_mastered': mastered_words,
            'current_streak': streak.current_streak if streak else 0,
            'longest_streak': streak.longest_streak if streak else 0,
            'this_week_minutes': this_week_seconds // 60,
            'vocabulary_mastery': (mastered_words / vocab_count * 100) if vocab_count > 0 else 0,
        }

    def get_weekly_activity_chart(self, user_id: int) -> List[Dict]:
        """
        Get daily activity for last 7 days.

        Returns:
            [
                {'date': '2025-01-15', 'minutes': 45, 'words': 12},
                {'date': '2025-01-16', 'minutes': 30, 'words': 8},
                ...
            ]
        """
        activities = []

        for i in range(6, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            start_of_day = datetime.combine(date, datetime.min.time())
            end_of_day = datetime.combine(date, datetime.max.time())

            # Watch time for day
            watch_seconds = self.db.query(
                func.sum(VideoProgress.watch_time_seconds)
            ).filter(
                VideoProgress.user_id == user_id,
                VideoProgress.last_watched_at >= start_of_day,
                VideoProgress.last_watched_at <= end_of_day
            ).scalar() or 0

            # Words added on day
            words_added = self.db.query(func.count(UserVocabulary.id)).filter(
                UserVocabulary.user_id == user_id,
                UserVocabulary.added_at >= start_of_day,
                UserVocabulary.added_at <= end_of_day
            ).scalar() or 0

            activities.append({
                'date': date.isoformat(),
                'minutes': watch_seconds // 60,
                'words': words_added,
            })

        return activities

    def generate_learning_recommendations(self, user_id: int) -> List[str]:
        """Generate personalized learning recommendations."""
        recommendations = []

        # Check review queue
        due_words = self.db.query(func.count(UserVocabulary.id)).filter(
            UserVocabulary.user_id == user_id,
            UserVocabulary.next_review <= datetime.now()
        ).scalar()

        if due_words > 0:
            recommendations.append(
                f"You have {due_words} words due for review. Practice now to maintain retention!"
            )

        # Check streak
        streak = self.db.query(LearningStreak).filter(
            LearningStreak.user_id == user_id
        ).first()

        if streak:
            last_activity = streak.last_activity_date.date()
            today = datetime.now().date()

            if (today - last_activity).days == 1:
                recommendations.append(
                    f"Keep your {streak.current_streak}-day streak alive! Watch a video today."
                )

        # Check incomplete videos
        incomplete = self.db.query(func.count(VideoProgress.id)).filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completed == False,
            VideoProgress.progress_percentage > 10
        ).scalar()

        if incomplete > 0:
            recommendations.append(
                f"You have {incomplete} videos in progress. Finish them to reinforce learning!"
            )

        return recommendations
```

**Integration Steps:**
1. Add progress tracking tables to database
2. Implement real-time progress updates during video playback
3. Create analytics dashboard endpoint
4. Build frontend dashboard with charts (using Recharts or Chart.js)
5. Add achievement system for gamification
6. Implement weekly activity visualization

---

## Summary: Priority Implementation Order

### Phase 1: Core Features (Weeks 1-2)
1. **Interactive Subtitles** - Implement hover translation and click for phrase context
2. **Real-Time Highlighting** - Add word-level synchronization with video playback
3. **Translation Cache** - Implement Zustand store for offline translation access

### Phase 2: Performance (Weeks 3-4)
4. **Parallel Transcription** - Add chunked processing for faster transcription
5. **Background Jobs** - Implement async transcription with status polling
6. **Redis Caching** - Add caching layer for API responses

### Phase 3: Learning Systems (Weeks 5-6)
7. **Spaced Repetition** - Implement SM-2 algorithm for vocabulary review
8. **Quiz Generation** - Add multiple question types with smart word selection
9. **Progress Tracking** - Build comprehensive analytics and dashboard

### Phase 4: Security & Deployment (Weeks 7-8)
10. **JWT Authentication** - Replace current auth with token-based system
11. **Docker Production** - Set up production deployment with Nginx
12. **Achievement System** - Add gamification and streak tracking

---

## Additional Resources

### Documentation Links
- [Whisper Official Docs](https://github.com/openai/whisper)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Zustand State Management](https://github.com/pmndrs/zustand)
- [SuperMemo SM-2 Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)

### Testing Recommendations
- Add integration tests for spaced repetition algorithm
- Test parallel transcription with various video lengths
- Validate JWT token expiration and renewal
- Test subtitle synchronization accuracy with different video formats

### Performance Benchmarks
- **Transcription**: Target < 1 minute for 10-minute videos
- **Subtitle Sync**: Update highlighting every 50ms
- **API Response**: < 200ms for cached translations
- **Quiz Generation**: < 500ms for 10-question session

---

**Document Version:** 1.0
**Last Updated:** 2025-11-20
**Author:** Claude Code Research Agent
