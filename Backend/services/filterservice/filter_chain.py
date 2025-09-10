import logging

logger = logging.getLogger(__name__)

"""
Subtitle Filter Chain Implementation
Chain of Command pattern for processing subtitles
"""

from typing import List, Dict, Any
from .interface import ISubtitleFilter, ISubtitleFilterChain, FilteredSubtitle, FilteringResult, FilteredWord


class SubtitleFilterChain(ISubtitleFilterChain):
    """
    Implementation of the subtitle filter chain
    Processes subtitles through a sequence of filters using Chain of Command pattern
    """
    
    def __init__(self):
        self._filters: List[ISubtitleFilter] = []
        self._statistics: Dict[str, Dict[str, Any]] = {}
    
    def add_filter(self, filter_impl: ISubtitleFilter) -> 'SubtitleFilterChain':
        """Add a filter to the chain"""
        self._filters.append(filter_impl)
        return self
    
    def process(self, subtitles: List[FilteredSubtitle]) -> FilteringResult:
        """
        Process subtitles through the entire filter chain
        """
        # Start with input subtitles
        current_subtitles = subtitles.copy()
        
        # Apply each filter in sequence
        for filter_impl in self._filters:
            logger.debug(f"Applying filter: {filter_impl.filter_name}")
            
            # Apply filter
            current_subtitles = filter_impl.filter(current_subtitles)
            
            # Collect statistics
            self._statistics[filter_impl.filter_name] = filter_impl.get_statistics()
        
        # Categorize results after all filters have been applied
        return self._categorize_results(current_subtitles)
    
    def get_filter_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics from all filters in the chain"""
        return self._statistics.copy()
    
    async def process_file(self, srt_file_path: str, user_id: int) -> Dict[str, Any]:
        """
        Process an SRT file through the filter chain
        
        Args:
            srt_file_path: Path to the SRT subtitle file
            user_id: User ID for personalized filtering
            
        Returns:
            Dictionary with filtered results
        """
        try:
            # For now, return mock filtered data
            # In a real implementation, this would:
            # 1. Parse the SRT file
            # 2. Convert to FilteredSubtitle objects  
            # 3. Run through the filter chain
            # 4. Return categorized results
            
            # Mock vocabulary words that would be extracted
            from ...api.models.vocabulary import VocabularyWord
            blocking_words = [
                VocabularyWord(word="schwierig", definition="difficult", difficulty_level="B2", known=False),
                VocabularyWord(word="verstehen", definition="to understand", difficulty_level="A2", known=False),
                VocabularyWord(word="komplex", definition="complex", difficulty_level="B1", known=False)
            ]
            
            return {
                "blocking_words": blocking_words,
                "learning_subtitles": [],
                "empty_subtitles": [],
                "statistics": {
                    "total_words": 150,
                    "filtered_words": 3,
                    "user_id": user_id,
                    "file_processed": srt_file_path
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing file {srt_file_path}: {e}")
            return {
                "blocking_words": [],
                "learning_subtitles": [], 
                "empty_subtitles": [],
                "statistics": {"error": str(e)}
            }
    
    def _categorize_results(self, subtitles: List[FilteredSubtitle]) -> FilteringResult:
        """
        Categorize filtered subtitles into learning content, blockers, and empty
        """
        learning_subtitles = []
        blocker_words = []
        empty_subtitles = []
        
        total_words = 0
        active_words = 0
        filtered_words = 0
        
        for subtitle in subtitles:
            total_words += len(subtitle.words)
            active_words += len(subtitle.active_words)
            filtered_words += len(subtitle.words) - len(subtitle.active_words)
            
            if subtitle.has_learning_content:
                # Subtitle has 2+ active words - good for learning
                learning_subtitles.append(subtitle)
            elif subtitle.is_blocker:
                # Single active word - collect as blocker
                blocker_words.extend(subtitle.active_words)
            else:
                # No active words - empty subtitle
                empty_subtitles.append(subtitle)
        
        # Compile statistics
        statistics = {
            "total_subtitles": len(subtitles),
            "learning_subtitles": len(learning_subtitles),
            "blocker_subtitles": len(blocker_words),
            "empty_subtitles": len(empty_subtitles),
            "total_words": total_words,
            "active_words": active_words,
            "filtered_words": filtered_words,
            "filter_rate": filtered_words / max(total_words, 1),
            "learning_rate": len(learning_subtitles) / max(len(subtitles), 1)
        }
        
        return FilteringResult(
            learning_subtitles=learning_subtitles,
            blocker_words=blocker_words,
            empty_subtitles=empty_subtitles,
            statistics=statistics
        )


class BaseSubtitleFilter(ISubtitleFilter):
    """
    Base class for subtitle filters with common functionality
    """
    
    def __init__(self):
        self._processed_words = 0
        self._filtered_words = 0
    
    def filter(self, subtitles: List[FilteredSubtitle]) -> List[FilteredSubtitle]:
        """
        Apply filter with statistics tracking
        """
        self._processed_words = 0
        self._filtered_words = 0
        
        for subtitle in subtitles:
            for word in subtitle.words:
                self._processed_words += 1
                
                # Only process words that are still active
                if word.status.value == "active":
                    if self._should_filter_word(word, subtitle):
                        word.status = self._get_filter_status()
                        word.filter_reason = self._get_filter_reason(word)
                        self._filtered_words += 1
        
        return subtitles
    
    def _should_filter_word(self, word: FilteredWord, subtitle: FilteredSubtitle) -> bool:
        """
        Override in subclasses to implement filtering logic
        """
        return False
    
    def _get_filter_status(self):
        """
        Override in subclasses to return appropriate WordStatus
        """
        from .interface import WordStatus
        return WordStatus.FILTERED_OTHER
    
    def _get_filter_reason(self, word: FilteredWord) -> str:
        """
        Override in subclasses to provide filter reason
        """
        return f"Filtered by {self.filter_name}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for this filter"""
        return {
            "processed_words": self._processed_words,
            "filtered_words": self._filtered_words,
            "filter_rate": self._filtered_words / max(self._processed_words, 1)
        }