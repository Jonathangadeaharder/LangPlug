"""
Direct Subtitle Processing - Simplified replacement for filter chain
Combines all filtering logic into a single, efficient processing function
"""

import logging
import re
from typing import List, Dict, Any, Set, Optional
from datetime import datetime

from .interface import FilteredSubtitle, FilteredWord, WordStatus, FilteringResult
from core.database import get_async_session
from database.models import UserLearningProgress, Vocabulary
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DirectSubtitleProcessor:
    """
    Simplified subtitle processor that replaces the Chain of Responsibility pattern
    with direct, efficient processing combining all filter logic
    """
    
    def __init__(self):
        pass
        
        # Pre-compiled patterns for efficiency
        self._proper_name_pattern = re.compile(r"^[A-Z][a-z]+$")
        self._non_alphabetic_pattern = re.compile(r"^[^a-zA-Z]*$")
        self._contains_numbers = re.compile(r"\d")
        self._word_pattern = re.compile(r'\b\w+\b')
        
        # Language-specific interjections (German for Superstore)
        self._german_interjections = {
            'ach', 'ah', 'äh', 'ähm', 'also', 'eh', 'hm', 'hmm', 'na', 'oh', 'oje', 
            'ok', 'okay', 'so', 'tja', 'uh', 'uhm', 'um', 'ups', 'wow', 'ja', 'nein',
            'doch', 'hallo', 'hey', 'hi', 'tschüss', 'bye'
        }
        
        # Cache for word difficulty and user knowledge
        self._word_difficulty_cache: Dict[str, str] = {}
        self._user_known_words_cache: Dict[str, Set[str]] = {}
        
    async def process_subtitles(self, subtitles: List[FilteredSubtitle], user_id: int, 
                         user_level: str = "A1", language: str = "de") -> FilteringResult:
        """
        Process subtitles with all filtering logic combined for efficiency
        
        Args:
            subtitles: List of subtitle objects to process
            user_id: User ID for personalized filtering
            user_level: User's language level (A1, A2, B1, B2, C1, C2)
            language: Target language code
            
        Returns:
            FilteringResult with categorized content
        """
        logger.info(f"Processing {len(subtitles)} subtitles for user {user_id}")
        
        # Pre-load user's known words for efficiency
        user_known_words = await self._get_user_known_words(user_id, language)
        
        # Pre-load difficulty levels if needed
        if not self._word_difficulty_cache:
            await self._load_word_difficulties(language)
        
        # Process each subtitle
        learning_subtitles = []
        blocker_words = []
        empty_subtitles = []
        
        total_words = 0
        active_words = 0
        filtered_words = 0
        
        for subtitle in subtitles:
            # Process words in this subtitle
            processed_words = []
            subtitle_active_words = []
            
            for word in subtitle.words:
                total_words += 1
                processed_word = self._process_word(word, user_known_words, user_level, language)
                processed_words.append(processed_word)
                
                if processed_word.status == WordStatus.ACTIVE:
                    subtitle_active_words.append(processed_word)
                    active_words += 1
                else:
                    filtered_words += 1
            
            # Update subtitle with processed words
            subtitle.words = processed_words
            
            # Categorize subtitle based on active words
            active_count = len(subtitle_active_words)
            
            if active_count >= 2:
                # Good for learning - has multiple unknown words
                learning_subtitles.append(subtitle)
            elif active_count == 1:
                # Single blocking word
                blocker_words.extend(subtitle_active_words)
            else:
                # No learning content
                empty_subtitles.append(subtitle)
        
        # Compile statistics
        statistics = {
            "total_subtitles": len(subtitles),
            "learning_subtitles": len(learning_subtitles),
            "blocker_words": len(blocker_words),
            "empty_subtitles": len(empty_subtitles),
            "total_words": total_words,
            "active_words": active_words,
            "filtered_words": filtered_words,
            "filter_rate": filtered_words / max(total_words, 1),
            "learning_rate": len(learning_subtitles) / max(len(subtitles), 1),
            "processing_time": datetime.now().isoformat(),
            "user_id": user_id,
            "user_level": user_level,
            "language": language
        }
        
        logger.info(f"Processing complete: {len(learning_subtitles)} learning subtitles, "
                   f"{len(blocker_words)} blocker words, {len(empty_subtitles)} empty subtitles")
        
        return FilteringResult(
            learning_subtitles=learning_subtitles,
            blocker_words=blocker_words,
            empty_subtitles=empty_subtitles,
            statistics=statistics
        )
    
    def _process_word(self, word: FilteredWord, user_known_words: Set[str], 
                     user_level: str, language: str) -> FilteredWord:
        """
        Apply all filtering logic to a single word efficiently
        """
        word_text = word.text.lower().strip()
        
        # 1. Basic vocabulary filter - filter out non-learning words
        if self._is_non_vocabulary_word(word_text, language):
            word.status = WordStatus.FILTERED_NON_VOCABULARY
            word.filter_reason = "Non-vocabulary word (interjection, proper name, etc.)"
            return word
        
        # 2. User knowledge filter - filter out known words
        if word_text in user_known_words:
            word.status = WordStatus.FILTERED_KNOWN
            word.filter_reason = "User already knows this word"
            return word
        
        # 3. Difficulty level filter - identify learning targets
        word_difficulty = self._get_word_difficulty(word_text, language)
        user_level_rank = self._get_level_rank(user_level)
        word_level_rank = self._get_level_rank(word_difficulty)
        
        if word_level_rank <= user_level_rank:
            # Word is at or below user level - should be known
            word.status = WordStatus.FILTERED_TOO_EASY
            word.filter_reason = f"Word level ({word_difficulty}) at or below user level ({user_level})"
            return word
        
        # Word passed all filters - it's a learning target
        word.status = WordStatus.ACTIVE
        word.metadata = {
            "difficulty_level": word_difficulty,
            "user_level": user_level,
            "language": language
        }
        return word
    
    def _is_non_vocabulary_word(self, word_text: str, language: str) -> bool:
        """Check if word should be filtered as non-vocabulary"""
        # Very short words
        if len(word_text) <= 2:
            return True
        
        # Contains numbers
        if self._contains_numbers.search(word_text):
            return True
        
        # Non-alphabetic content
        if self._non_alphabetic_pattern.match(word_text):
            return True
        
        # Language-specific interjections
        if language == "de" and word_text in self._german_interjections:
            return True
        
        # Proper names (basic check)
        if self._proper_name_pattern.match(word_text):
            return True
        
        return False
    
    async def _get_user_known_words(self, user_id: int, language: str) -> Set[str]:
        """Get set of words the user already knows"""
        cache_key = f"{user_id}_{language}"
        
        if cache_key not in self._user_known_words_cache:
            try:
                async with get_async_session() as session:
                    query = select(UserVocabulary.word).where(
                        UserVocabulary.user_id == user_id,
                        UserVocabulary.language == language,
                        UserVocabulary.known == True
                    ).distinct()
                    
                    result = await session.execute(query)
                    known_words = {word.lower() for (word,) in result.fetchall()}
                    self._user_known_words_cache[cache_key] = known_words
                    logger.debug(f"Loaded {len(known_words)} known words for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error loading user known words: {e}")
                self._user_known_words_cache[cache_key] = set()
        
        return self._user_known_words_cache[cache_key]
    
    async def _load_word_difficulties(self, language: str):
        """Pre-load word difficulty levels for efficiency"""
        try:
            async with get_async_session() as session:
                query = select(Vocabulary.word, Vocabulary.difficulty_level).where(
                    Vocabulary.language == language
                ).distinct()
                
                result = await session.execute(query)
                rows = result.fetchall()
                
                for word, difficulty in rows:
                    self._word_difficulty_cache[word.lower()] = difficulty
                
                logger.debug(f"Loaded {len(self._word_difficulty_cache)} word difficulties")
                
        except Exception as e:
            logger.error(f"Error loading word difficulties: {e}")
    
    def _get_word_difficulty(self, word_text: str, language: str) -> str:
        """Get difficulty level for a word"""
        return self._word_difficulty_cache.get(word_text, "B1")  # Default to B1 if unknown
    
    def _get_level_rank(self, level: str) -> int:
        """Convert CEFR level to numeric rank for comparison"""
        level_ranks = {
            "A1": 1, "A2": 2, "B1": 3, 
            "B2": 4, "C1": 5, "C2": 6
        }
        return level_ranks.get(level.upper(), 3)  # Default to B1 level
    
    async def process_srt_file(self, srt_file_path: str, user_id: int, 
                        user_level: str = "A1", language: str = "de") -> Dict[str, Any]:
        """
        Process an SRT file directly - simplified version of filter chain process_file
        """
        try:
            from ..utils.srt_parser import SRTParser
            from api.models.processing import VocabularyWord
            
            logger.info(f"Processing SRT file: {srt_file_path}")
            
            # Parse SRT file
            srt_segments = SRTParser.parse_file(srt_file_path)
            logger.info(f"Parsed {len(srt_segments)} subtitle segments")
            
            # Convert to FilteredSubtitle objects
            filtered_subtitles = []
            for segment in srt_segments:
                words = self._extract_words_from_text(segment.text, segment.start_time, segment.end_time)
                
                filtered_subtitle = FilteredSubtitle(
                    original_text=segment.text,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    words=words
                )
                filtered_subtitles.append(filtered_subtitle)
            
            # Process through simplified filtering
            filtering_result = await self.process_subtitles(filtered_subtitles, user_id, user_level, language)
            
            # Convert blocker words to VocabularyWord objects
            blocking_words = []
            for word in filtering_result.blocker_words:
                vocab_word = VocabularyWord(
                    word=word.text,
                    definition="",
                    difficulty_level=word.metadata.get("difficulty_level", "Unknown"),
                    known=False
                )
                blocking_words.append(vocab_word)
            
            return {
                "blocking_words": blocking_words,
                "learning_subtitles": filtering_result.learning_subtitles,
                "empty_subtitles": filtering_result.empty_subtitles,
                "statistics": {
                    **filtering_result.statistics,
                    "file_processed": srt_file_path,
                    "segments_parsed": len(srt_segments)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing file {srt_file_path}: {e}", exc_info=True)
            return {
                "blocking_words": [],
                "learning_subtitles": [],
                "empty_subtitles": [],
                "statistics": {"error": str(e)}
            }
    
    def _extract_words_from_text(self, text: str, start_time: float, end_time: float) -> List[FilteredWord]:
        """Extract words from subtitle text and create FilteredWord objects"""
        word_matches = list(self._word_pattern.finditer(text.lower()))
        words = []
        
        # Estimate timing for each word
        duration = end_time - start_time
        word_duration = duration / max(len(word_matches), 1)
        
        for i, match in enumerate(word_matches):
            word_text = match.group()
            word_start = start_time + (i * word_duration)
            word_end = word_start + word_duration
            
            filtered_word = FilteredWord(
                text=word_text,
                start_time=word_start,
                end_time=word_end,
                status=WordStatus.ACTIVE,
                filter_reason=None,
                confidence=None,
                metadata={}
            )
            words.append(filtered_word)
        
        return words
