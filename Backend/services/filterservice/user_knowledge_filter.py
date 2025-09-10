"""
User Knowledge Filter
Filters out words that the user already knows (requires authentication)
"""

from typing import Set, Optional
from .interface import FilteredWord, WordStatus, IUserVocabularyService
from .filter_chain import BaseSubtitleFilter

try:
    from ..loggingservice.logging_service import get_logger, log_user_action, log_error
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from services.loggingservice.logging_service import get_logger, log_user_action, log_error


class UserKnowledgeFilter(BaseSubtitleFilter):
    """
    Filters out words that the user already knows
    Uses authenticated IUserVocabularyService to check user's known vocabulary
    """
    
    def __init__(self, vocabulary_service: IUserVocabularyService, session_token: str, user_id: str, language: str = "en"):
        super().__init__()
        self.vocabulary_service = vocabulary_service
        self.session_token = session_token
        self.user_id = user_id
        self.language = language
        self.logger = get_logger("user_knowledge_filter")
        
        # Cache known words for performance
        self._known_words_cache: Optional[Set[str]] = None
        self._cache_initialized = False
        
        # Statistics
        self._known_words_filtered = 0
        self._cache_refresh_count = 0
    
    @property
    def filter_name(self) -> str:
        return "UserKnowledgeFilter"
    
    def _initialize_cache(self):
        """Initialize the known words cache with authentication"""
        try:
            self._known_words_cache = self.vocabulary_service.get_known_words(
                self.session_token, self.user_id, self.language
            )
            self._cache_initialized = True
            self._cache_refresh_count += 1
            
            self.logger.info(f"Initialized knowledge cache for user {self.user_id}: {len(self._known_words_cache)} known words")
            
        except Exception as e:
            log_error("user_knowledge_filter", e, 
                     operation="cache_initialization", user_id=self.user_id, language=self.language)
            self._known_words_cache = set()  # Empty cache on auth failure
            self._cache_initialized = False
    
    def _ensure_cache_initialized(self):
        """Ensure cache is initialized before use"""
        if not self._cache_initialized:
            self._initialize_cache()
    
    def _should_filter_word(self, word: FilteredWord, subtitle) -> bool:
        """Check if word should be filtered because user knows it"""
        self._ensure_cache_initialized()
        
        text = word.text.lower().strip()
        
        # Skip empty or very short words
        if len(text) < 2:
            return False
        
        # Check if user knows this word
        is_known = text in self._known_words_cache if self._known_words_cache else False
        
        if is_known:
            self._known_words_filtered += 1
            self.logger.debug(f"Filtered known word: '{text}' for user {self.user_id}")
            return True
        
        return False
    
    def _get_filter_status(self):
        return WordStatus.FILTERED_KNOWN
    
    def _get_filter_reason(self, word: FilteredWord) -> str:
        return f"User {self.user_id} already knows this word"
    
    def refresh_cache(self):
        """
        Manually refresh the known words cache
        Useful when user learns new words during processing
        """
        self.logger.info(f"Refreshing knowledge cache for user {self.user_id}")
        self._initialize_cache()
    
    def mark_word_learned(self, word: str) -> bool:
        """
        Mark a word as learned and update the cache
        
        Args:
            word: Word to mark as learned
            
        Returns:
            True if word was successfully marked as learned
        """
        try:
            result = self.vocabulary_service.mark_word_learned(
                self.session_token, self.user_id, word, self.language
            )
            
            if result and self._known_words_cache is not None:
                # Update local cache
                self._known_words_cache.add(word.lower().strip())
                self.logger.info(f"Marked word '{word}' as learned for user {self.user_id}")
                
                # Log user action
                log_user_action(self.user_id, "learn", f"word:{word}", True, 
                               language=self.language, cache_size=len(self._known_words_cache))
            
            return result
            
        except Exception as e:
            log_user_action(self.user_id, "learn", f"word:{word}", False, error=str(e))
            log_error("user_knowledge_filter", e, 
                     operation="mark_word_learned", word=word, user_id=self.user_id)
            return False
    
    def get_cache_status(self) -> dict:
        """Get information about the cache status"""
        return {
            "initialized": self._cache_initialized,
            "cache_size": len(self._known_words_cache) if self._known_words_cache else 0,
            "refresh_count": self._cache_refresh_count,
            "user_id": self.user_id,
            "language": self.language
        }
    
    def get_statistics(self):
        base_stats = super().get_statistics()
        cache_stats = self.get_cache_status()
        
        base_stats.update({
            "known_words_filtered": self._known_words_filtered,
            "cache_initialized": cache_stats["initialized"],
            "cache_size": cache_stats["cache_size"],
            "cache_refresh_count": cache_stats["refresh_count"],
            "user_id": self.user_id,
            "language": self.language
        })
        return base_stats