"""
Domain services for vocabulary operations.
Contains business logic that doesn't naturally fit within entities.
"""

from datetime import datetime, timedelta
from typing import Any

from .entities import ConfidenceLevel, DifficultyLevel, LearningSession, UserVocabularyProgress, VocabularyWord


class VocabularyDifficultyAnalyzer:
    """Domain service for analyzing and determining vocabulary difficulty"""

    @staticmethod
    def analyze_word_difficulty(
        word: str, language: str, frequency_rank: int | None = None, context: str | None = None
    ) -> DifficultyLevel:
        """Analyze and determine difficulty level for a word"""

        # Basic length-based heuristics
        word_length = len(word)

        # Frequency-based analysis
        if frequency_rank:
            if frequency_rank <= 1000:
                base_level = DifficultyLevel.A1
            elif frequency_rank <= 3000:
                base_level = DifficultyLevel.A2
            elif frequency_rank <= 5000:
                base_level = DifficultyLevel.B1
            elif frequency_rank <= 8000:
                base_level = DifficultyLevel.B2
            else:
                base_level = DifficultyLevel.C1
        # Fallback to length-based heuristics
        elif word_length <= 4:
            base_level = DifficultyLevel.A1
        elif word_length <= 7:
            base_level = DifficultyLevel.A2
        elif word_length <= 10:
            base_level = DifficultyLevel.B1
        elif word_length <= 13:
            base_level = DifficultyLevel.B2
        else:
            base_level = DifficultyLevel.C1

        # Language-specific adjustments
        if language == "de":  # German
            # German compound words can be very long but not necessarily difficult
            if word_length > 15 and word.count("ß") == 0:
                # Likely compound word, adjust down
                adjustment = -1
            else:
                adjustment = 0
        else:
            adjustment = 0

        # Apply adjustment
        new_level_value = max(1, min(5, base_level.value + adjustment))
        return DifficultyLevel(
            f"{'ABCDEFG'[new_level_value - 1]}{1 if new_level_value <= 2 else 2 if new_level_value <= 4 else 1}"
        )

    @staticmethod
    def should_words_be_grouped(words: list[VocabularyWord]) -> dict[str, list[VocabularyWord]]:
        """Determine if words should be grouped for learning"""
        groups = {"similar_difficulty": [], "word_families": [], "thematic_groups": []}

        # Group by difficulty level
        difficulty_groups = {}
        for word in words:
            level = word.difficulty_level
            if level not in difficulty_groups:
                difficulty_groups[level] = []
            difficulty_groups[level].append(word)

        # Find groups with similar difficulty
        for level, group_words in difficulty_groups.items():
            if len(group_words) >= 3:
                groups["similar_difficulty"].extend(group_words)

        # Additional grouping logic can be added here:
        # - Word families (e.g., laufen, läuft, gelaufen) using lemmatization
        # - Thematic groups (e.g., colors, food, family) using semantic analysis
        # - Frequency-based groups for common vs rare words

        return groups


class LearningProgressCalculator:
    """Domain service for calculating learning progress and recommendations"""

    @staticmethod
    def calculate_user_level(progress_records: list[UserVocabularyProgress]) -> DifficultyLevel:
        """Calculate user's overall language level based on progress"""
        if not progress_records:
            return DifficultyLevel.A1

        # Group by difficulty level
        level_stats = {}
        for progress in progress_records:
            level = progress.vocabulary_word.difficulty_level
            if level not in level_stats:
                level_stats[level] = {"total": 0, "known": 0}

            level_stats[level]["total"] += 1
            if progress.is_known and progress.confidence_level.value >= ConfidenceLevel.MODERATE.value:
                level_stats[level]["known"] += 1

        # Calculate mastery percentage for each level
        level_mastery = {}
        for level, stats in level_stats.items():
            mastery_pct = stats["known"] / stats["total"] if stats["total"] > 0 else 0
            level_mastery[level] = mastery_pct

        # Determine user level based on mastery
        for level in [
            DifficultyLevel.C1,
            DifficultyLevel.B2,
            DifficultyLevel.B1,
            DifficultyLevel.A2,
            DifficultyLevel.A1,
        ]:
            if level in level_mastery and level_mastery[level] >= 0.7:
                return level

        return DifficultyLevel.A1

    @staticmethod
    def calculate_next_learning_words(
        progress_records: list[UserVocabularyProgress],
        target_count: int = 10,
        focus_level: DifficultyLevel | None = None,
    ) -> list[VocabularyWord]:
        """Calculate which words user should learn next"""

        # Words that need review (highest priority)
        needs_review = [p.vocabulary_word for p in progress_records if p.needs_review and not p.is_mastered]

        # Words that are partially known (medium priority)
        partially_known = [
            p.vocabulary_word
            for p in progress_records
            if not p.is_known and p.confidence_level.value > ConfidenceLevel.UNKNOWN.value
        ]

        # Unknown words at appropriate level (lowest priority)
        unknown_words = [
            p.vocabulary_word
            for p in progress_records
            if not p.is_known and p.confidence_level == ConfidenceLevel.UNKNOWN
        ]

        # Filter by focus level if specified
        if focus_level:
            needs_review = [w for w in needs_review if w.difficulty_level == focus_level]
            partially_known = [w for w in partially_known if w.difficulty_level == focus_level]
            unknown_words = [w for w in unknown_words if w.difficulty_level == focus_level]

        # Combine in priority order
        recommended = []

        # Add words needing review first
        recommended.extend(needs_review[:target_count])
        remaining = target_count - len(recommended)

        # Add partially known words
        if remaining > 0:
            recommended.extend(partially_known[:remaining])
            remaining = target_count - len(recommended)

        # Add unknown words
        if remaining > 0:
            recommended.extend(unknown_words[:remaining])

        return recommended[:target_count]

    @staticmethod
    def calculate_learning_streak(sessions: list[LearningSession]) -> int:
        """Calculate current learning streak in days"""
        if not sessions:
            return 0

        # Sort sessions by date (most recent first)
        sorted_sessions = sorted(sessions, key=lambda s: s.completed_at or datetime.min, reverse=True)

        streak = 0
        current_date = datetime.utcnow().date()

        for session in sorted_sessions:
            if not session.completed_at:
                continue

            session_date = session.completed_at.date()

            # Check if session is from today or consecutive days
            expected_date = current_date - timedelta(days=streak)

            if session_date == expected_date:
                streak += 1
                current_date = session_date
            else:
                break

        return streak

    @staticmethod
    def generate_progress_insights(
        progress_records: list[UserVocabularyProgress], sessions: list[LearningSession]
    ) -> dict[str, Any]:
        """Generate insights about user's learning progress"""

        if not progress_records:
            return {"message": "No learning data available yet"}

        # Basic statistics
        total_words = len(progress_records)
        known_words = len([p for p in progress_records if p.is_known])
        mastered_words = len([p for p in progress_records if p.is_mastered])

        # Level breakdown
        level_breakdown = {}
        for progress in progress_records:
            level = progress.vocabulary_word.difficulty_level.value
            if level not in level_breakdown:
                level_breakdown[level] = {"total": 0, "known": 0, "mastered": 0}

            level_breakdown[level]["total"] += 1
            if progress.is_known:
                level_breakdown[level]["known"] += 1
            if progress.is_mastered:
                level_breakdown[level]["mastered"] += 1

        # Recent performance
        recent_sessions = [
            s for s in sessions if s.completed_at and s.completed_at > datetime.utcnow() - timedelta(days=7)
        ]

        recent_accuracy = 0
        if recent_sessions:
            total_answers = sum(s.correct_answers + s.incorrect_answers for s in recent_sessions)
            correct_answers = sum(s.correct_answers for s in recent_sessions)
            recent_accuracy = correct_answers / total_answers if total_answers > 0 else 0

        # Learning velocity (words learned per week)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recently_learned = len([p for p in progress_records if p.first_learned_at and p.first_learned_at > week_ago])

        return {
            "total_words": total_words,
            "known_words": known_words,
            "mastered_words": mastered_words,
            "knowledge_percentage": (known_words / total_words * 100) if total_words > 0 else 0,
            "mastery_percentage": (mastered_words / total_words * 100) if total_words > 0 else 0,
            "level_breakdown": level_breakdown,
            "recent_accuracy": round(recent_accuracy * 100, 1),
            "learning_velocity": recently_learned,
            "current_streak": LearningProgressCalculator.calculate_learning_streak(sessions),
            "estimated_level": LearningProgressCalculator.calculate_user_level(progress_records).value,
        }


class SpacedRepetitionScheduler:
    """Domain service for spaced repetition scheduling"""

    @staticmethod
    def calculate_optimal_review_interval(progress: UserVocabularyProgress) -> timedelta:
        """Calculate optimal interval for spaced repetition"""

        # Base intervals in hours for each confidence level
        base_intervals = {
            ConfidenceLevel.UNKNOWN: 1,
            ConfidenceLevel.WEAK: 4,
            ConfidenceLevel.MODERATE: 24,
            ConfidenceLevel.STRONG: 72,
            ConfidenceLevel.MASTERED: 168,
        }

        base_hours = base_intervals[progress.confidence_level]

        # Adjust based on success rate
        success_rate = progress.success_rate
        if success_rate >= 0.9:
            multiplier = 1.5
        elif success_rate >= 0.7:
            multiplier = 1.2
        elif success_rate >= 0.5:
            multiplier = 1.0
        else:
            multiplier = 0.7

        # Adjust based on learning streak
        if progress.learning_streak >= 5:
            multiplier *= 1.3
        elif progress.learning_streak >= 3:
            multiplier *= 1.1

        # Apply difficulty adjustment
        multiplier *= progress.difficulty_adjustment

        # Calculate final interval
        final_hours = int(base_hours * multiplier)

        # Ensure reasonable bounds
        final_hours = max(1, min(final_hours, 24 * 30))  # 1 hour to 30 days

        return timedelta(hours=final_hours)

    @staticmethod
    def get_words_due_for_review(
        progress_records: list[UserVocabularyProgress], max_words: int = 20
    ) -> list[UserVocabularyProgress]:
        """Get words that are due for review"""

        # Filter words that need review
        due_words = [p for p in progress_records if p.needs_review and not p.is_mastered]

        # Sort by priority (overdue words first, then by confidence level)
        def review_priority(progress: UserVocabularyProgress) -> tuple:
            if progress.next_review_at:
                overdue_hours = (datetime.utcnow() - progress.next_review_at).total_seconds() / 3600
                overdue_hours = max(0, overdue_hours)
            else:
                overdue_hours = 999  # Never reviewed words get highest priority

            # Lower confidence level = higher priority (lower number = higher priority in sort)
            confidence_priority = progress.confidence_level.value

            return (-overdue_hours, confidence_priority)

        due_words.sort(key=review_priority)

        return due_words[:max_words]
