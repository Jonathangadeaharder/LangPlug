"""
Result processing service for filtering operations
"""

import json
import logging
from pathlib import Path
from typing import Any

from services.filterservice.interface import FilteringResult

logger = logging.getLogger(__name__)


class ResultProcessorService:
    """Processes and formats filtering results"""

    async def process_filtering_results(
        self, filtering_result: FilteringResult, vocabulary_words: list
    ) -> dict[str, Any]:
        """
        Process and format filtering results

        Args:
            filtering_result: Raw filtering result from subtitle processor
            vocabulary_words: List of vocabulary words

        Returns:
            Formatted results dictionary
        """
        results = {
            "vocabulary_words": vocabulary_words,
            "learning_subtitles": len(filtering_result.learning_subtitles),
            "total_words": filtering_result.statistics.get("total_words", 0),
            "active_words": filtering_result.statistics.get("active_words", 0),
            "filter_rate": filtering_result.statistics.get("filter_rate", 0),
            "statistics": filtering_result.statistics,
        }

        return results

    def format_results(
        self, vocabulary_words: list, learning_subtitles_count: int, statistics: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Format results into standard structure

        Args:
            vocabulary_words: List of vocabulary words
            learning_subtitles_count: Count of learning subtitles
            statistics: Filtering statistics

        Returns:
            Formatted results dictionary
        """
        return {
            "vocabulary_words": vocabulary_words,
            "learning_subtitles": learning_subtitles_count,
            "total_words": statistics.get("total_words", 0),
            "active_words": statistics.get("active_words", 0),
            "filter_rate": statistics.get("filter_rate", 0),
            "statistics": statistics,
        }

    async def save_to_file(self, results: dict[str, Any], srt_path: str) -> str:
        """
        Save filtered results to JSON file

        Args:
            results: Results dictionary to save
            srt_path: Original SRT file path (used to determine output path)

        Returns:
            Path to saved file
        """
        output_path = Path(srt_path).with_suffix(".vocabulary.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved filtering results to {output_path}")
        return str(output_path)


# Global instance
result_processor_service = ResultProcessorService()


def get_result_processor_service() -> ResultProcessorService:
    """Get the global result processor service instance"""
    return result_processor_service
