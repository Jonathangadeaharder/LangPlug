"""
SM-2 Spaced Repetition Algorithm

Implements the SuperMemo SM-2 algorithm for optimal vocabulary review scheduling.
Research shows spaced repetition is one of the most effective learning techniques,
with retention rates 2-3x higher than massed practice.

Based on:
- Wozniak, P. A. (1990). SuperMemo algorithm SM-2
- Research from Vocabulary Builder project
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ReviewQuality(Enum):
    """
    User's self-assessed quality of recall (0-5).

    Based on SM-2 quality ratings:
    - 0-2: Failed recall (word forgotten)
    - 3-5: Successful recall (word remembered)
    """
    COMPLETE_BLACKOUT = 0      # Complete failure, no memory
    INCORRECT_EASY = 1          # Incorrect response, but seemed easy
    INCORRECT_HARD = 2          # Incorrect response, difficult
    CORRECT_HARD = 3            # Correct with serious difficulty
    CORRECT_HESITATION = 4      # Correct after hesitation
    PERFECT = 5                 # Perfect recall, immediate


@dataclass
class VocabularyReviewItem:
    """
    Vocabulary item with spaced repetition metadata.

    Attributes:
        word: The vocabulary word (lemma form)
        translation: Primary translation
        easiness_factor: SM-2 easiness (1.3-2.5), higher = easier
        repetitions: Number of successful consecutive reviews
        interval: Days until next review
        next_review: Datetime of next scheduled review
        last_reviewed: Datetime of last review
        total_reviews: Total number of reviews
        correct_reviews: Number of correct reviews
    """
    word: str
    translation: str
    easiness_factor: float = 2.5  # SM-2 default
    repetitions: int = 0
    interval: int = 1  # Days
    next_review: datetime | None = None
    last_reviewed: datetime | None = None
    total_reviews: int = 0
    correct_reviews: int = 0

    def __post_init__(self):
        if self.next_review is None:
            self.next_review = datetime.now()

    @property
    def success_rate(self) -> float:
        """Calculate percentage of correct reviews"""
        if self.total_reviews == 0:
            return 0.0
        return (self.correct_reviews / self.total_reviews) * 100

    @property
    def is_due(self) -> bool:
        """Check if item is due for review"""
        return datetime.now() >= self.next_review

    @property
    def is_new(self) -> bool:
        """Check if this is a new word (never reviewed)"""
        return self.total_reviews == 0

    @property
    def is_learning(self) -> bool:
        """Check if word is in learning phase (< 5 reviews)"""
        return 0 < self.repetitions < 5

    @property
    def is_mature(self) -> bool:
        """Check if word is mature (≥ 5 reviews, EF ≥ 2.5)"""
        return self.repetitions >= 5 and self.easiness_factor >= 2.5


class SM2Algorithm:
    """
    SuperMemo SM-2 algorithm implementation.

    The SM-2 algorithm calculates optimal review intervals based on:
    - Quality of recall (0-5)
    - Previous easiness factor
    - Number of consecutive successful reviews

    Research basis:
    - Proven to improve retention by 2-3x vs. massed practice
    - Optimal balance between review frequency and retention
    - Widely used in Anki, SuperMemo, and other SRS systems

    Example:
        ```python
        algorithm = SM2Algorithm()
        item = VocabularyReviewItem(word="hallo", translation="hello")

        # User recalls word perfectly
        updated_item = algorithm.calculate_next_review(
            item,
            ReviewQuality.PERFECT
        )

        print(f"Next review in {updated_item.interval} days")
        print(f"Easiness factor: {updated_item.easiness_factor:.2f}")
        ```
    """

    MIN_EASINESS = 1.3  # Minimum easiness factor (very difficult words)
    MAX_EASINESS = 2.5  # Maximum easiness factor (very easy words)

    def calculate_next_review(
        self,
        item: VocabularyReviewItem,
        quality: ReviewQuality
    ) -> VocabularyReviewItem:
        """
        Calculate next review interval using SM-2 algorithm.

        SM-2 Formula:
        - EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        - If q < 3: reset repetitions, interval = 1
        - If q >= 3:
            - First review: interval = 1
            - Second review: interval = 6
            - Subsequent: interval = previous_interval * EF'

        Args:
            item: Current vocabulary item
            quality: User's recall quality (0-5)

        Returns:
            Updated vocabulary item with new scheduling

        Example:
            >>> item = VocabularyReviewItem("hallo", "hello")
            >>> alg = SM2Algorithm()
            >>>
            >>> # Perfect recall
            >>> item = alg.calculate_next_review(item, ReviewQuality.PERFECT)
            >>> # interval=1, EF=2.6, repetitions=1
            >>>
            >>> # After 1 day, perfect recall again
            >>> item = alg.calculate_next_review(item, ReviewQuality.PERFECT)
            >>> # interval=6, EF=2.7, repetitions=2
            >>>
            >>> # After 6 days, correct with hesitation
            >>> item = alg.calculate_next_review(item, ReviewQuality.CORRECT_HESITATION)
            >>> # interval=16 (6*2.7), EF=2.6, repetitions=3
        """
        q = quality.value

        # Update statistics
        item.total_reviews += 1
        if q >= 3:
            item.correct_reviews += 1

        # Calculate new easiness factor
        # EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        new_ef = item.easiness_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(self.MIN_EASINESS, min(self.MAX_EASINESS, new_ef))

        # Update repetition count and interval
        if q < 3:
            # Failed recall - reset to beginning
            new_repetitions = 0
            new_interval = 1
            logger.debug(f"Word '{item.word}' failed recall (q={q}), resetting to interval=1")
        else:
            # Successful recall
            new_repetitions = item.repetitions + 1

            if new_repetitions == 1:
                # First successful review
                new_interval = 1
            elif new_repetitions == 2:
                # Second successful review
                new_interval = 6
            else:
                # Subsequent reviews: multiply previous interval by EF
                new_interval = int(item.interval * new_ef)
                # Cap maximum interval at 365 days (1 year)
                new_interval = min(new_interval, 365)

            logger.debug(
                f"Word '{item.word}' successful recall (q={q}): "
                f"interval={new_interval}, EF={new_ef:.2f}, reps={new_repetitions}"
            )

        # Calculate next review date
        next_review = datetime.now() + timedelta(days=new_interval)

        # Update item
        item.easiness_factor = new_ef
        item.repetitions = new_repetitions
        item.interval = new_interval
        item.next_review = next_review
        item.last_reviewed = datetime.now()

        return item

    def get_due_items(
        self,
        all_items: list[VocabularyReviewItem]
    ) -> list[VocabularyReviewItem]:
        """
        Get vocabulary items due for review, sorted by priority.

        Priority calculation:
        - Overdue items first (past next_review date)
        - Sorted by: overdue_duration * (1 / easiness_factor)
        - This prioritizes difficult words that are overdue

        Args:
            all_items: List of all vocabulary items

        Returns:
            Sorted list of due items (highest priority first)

        Example:
            >>> items = [item1, item2, item3, ...]
            >>> due = algorithm.get_due_items(items)
            >>> print(f"{len(due)} words due for review")
            >>>
            >>> for item in due[:10]:  # Review top 10
            >>>     print(f"{item.word}: overdue by {(now - item.next_review).days} days")
        """
        now = datetime.now()

        # Filter due items
        due_items = [item for item in all_items if item.next_review <= now]

        # Sort by priority: overdue duration * difficulty
        # Difficult words (low EF) get higher priority
        due_items.sort(
            key=lambda x: (
                (now - x.next_review).total_seconds() * (1 / x.easiness_factor)
            ),
            reverse=True
        )

        logger.info(f"Found {len(due_items)} due items out of {len(all_items)} total")

        return due_items

    def get_learning_stats(
        self,
        all_items: list[VocabularyReviewItem]
    ) -> dict:
        """
        Generate learning statistics for user dashboard.

        Returns:
            dict with:
                - total_words: Total vocabulary size
                - new_words: Never reviewed
                - learning: Currently learning (1-4 reviews)
                - mature: Mastered (≥5 reviews, EF≥2.5)
                - due_today: Due for review today
                - due_this_week: Due in next 7 days
                - overdue: Past due date
                - avg_easiness: Average easiness factor
                - success_rate: Overall success rate

        Example:
            >>> stats = algorithm.get_learning_stats(all_items)
            >>> print(f"Vocabulary: {stats['total_words']} words")
            >>> print(f"Due today: {stats['due_today']}")
            >>> print(f"Mastered: {stats['mature']} words")
            >>> print(f"Success rate: {stats['success_rate']:.1f}%")
        """
        now = datetime.now()
        today = now.date()
        next_week = today + timedelta(days=7)

        # Categorize items
        new_words = sum(1 for item in all_items if item.is_new)
        learning = sum(1 for item in all_items if item.is_learning)
        mature = sum(1 for item in all_items if item.is_mature)

        # Due items
        due_today = sum(
            1 for item in all_items
            if item.next_review.date() <= today
        )

        due_this_week = sum(
            1 for item in all_items
            if today < item.next_review.date() <= next_week
        )

        overdue = sum(
            1 for item in all_items
            if item.next_review < now
        )

        # Calculate averages
        reviewed_items = [item for item in all_items if item.total_reviews > 0]

        if reviewed_items:
            avg_easiness = sum(item.easiness_factor for item in reviewed_items) / len(reviewed_items)
            total_reviews = sum(item.total_reviews for item in reviewed_items)
            total_correct = sum(item.correct_reviews for item in reviewed_items)
            success_rate = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        else:
            avg_easiness = 2.5
            success_rate = 0

        return {
            'total_words': len(all_items),
            'new_words': new_words,
            'learning': learning,
            'mature': mature,
            'due_today': due_today,
            'due_this_week': due_this_week,
            'overdue': overdue,
            'avg_easiness': avg_easiness,
            'success_rate': success_rate,
        }
