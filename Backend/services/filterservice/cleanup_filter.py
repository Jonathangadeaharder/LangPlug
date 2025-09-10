"""
Cleanup Filter
Final filter to clean up and categorize processed subtitles
"""

from typing import List
from .interface import FilteredSubtitle, WordStatus
from .filter_chain import BaseSubtitleFilter


class CleanupFilter(BaseSubtitleFilter):
    """
    Final cleanup filter that:
    1. Filters subtitles that are too short in duration (< 0.5s)
    2. Provides final statistics
    3. Prepares subtitles for categorization
    """
    
    def __init__(self):
        super().__init__()
        
        # Statistics
        self._short_duration_filtered = 0
        self._empty_subtitles_found = 0
        self._single_word_subtitles = 0
        self._learning_subtitles = 0
    
    @property
    def filter_name(self) -> str:
        return "CleanupFilter"
    
    def filter(self, subtitles: List[FilteredSubtitle]) -> List[FilteredSubtitle]:
        """Perform final cleanup on subtitles"""
        self._processed_words = 0
        self._filtered_words = 0
        self._short_duration_filtered = 0
        self._empty_subtitles_found = 0
        self._single_word_subtitles = 0
        self._learning_subtitles = 0
        
        for subtitle in subtitles:
            # Count all words for statistics
            self._processed_words += len(subtitle.words)
            
            # Count active vs filtered words
            active_count = len(subtitle.active_words)
            total_count = len(subtitle.words)
            self._filtered_words += (total_count - active_count)
            
            # Check subtitle duration (filter if < 0.5 seconds)
            duration = subtitle.end_time - subtitle.start_time
            if duration < 0.5 and active_count > 0:
                self._short_duration_filtered += 1
                # Mark remaining active words as filtered due to short duration
                for word in subtitle.words:
                    if word.status == WordStatus.ACTIVE:
                        word.status = WordStatus.FILTERED_OTHER
                        word.filter_reason = "Subtitle too short"
                        self._filtered_words += 1
            
            # Count final categories
            final_active_count = len(subtitle.active_words)
            if final_active_count == 0:
                self._empty_subtitles_found += 1
            elif final_active_count == 1:
                self._single_word_subtitles += 1
            else:
                self._learning_subtitles += 1
        
        return subtitles
    
    def get_statistics(self):
        base_stats = super().get_statistics()
        base_stats.update({
            "empty_subtitles": self._empty_subtitles_found,
            "single_word_subtitles": self._single_word_subtitles,
            "learning_subtitles": self._learning_subtitles,
            "short_duration_filtered": self._short_duration_filtered
        })
        return base_stats