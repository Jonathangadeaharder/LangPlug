"""
Game Scoring Service

Handles answer evaluation and scoring logic.
Isolated from session management and question generation.
"""

from datetime import datetime

from core.config.logging_config import get_logger

logger = get_logger(__name__)


class AnswerEvaluation:
    """Result of answer evaluation"""

    def __init__(self, is_correct: bool, points_awarded: int):
        self.is_correct = is_correct
        self.points_awarded = points_awarded


class GameScoringService:
    """
    Service for evaluating answers and calculating scores

    Responsibilities:
        - Evaluate user answers against correct answers
        - Calculate points awarded
        - Provide answer feedback
    """

    def evaluate_answer(self, question: dict, user_answer: str, correct_answer: str | None = None) -> AnswerEvaluation:
        """
        Evaluate a user's answer against the correct answer

        Args:
            question: Question dictionary with metadata
            user_answer: User's submitted answer
            correct_answer: Override for correct answer (optional)

        Returns:
            AnswerEvaluation with is_correct and points_awarded
        """
        expected_answer = (question.get("correct_answer") or correct_answer or "").strip().lower()
        user_answer_normalized = user_answer.strip().lower()
        is_correct = expected_answer and user_answer_normalized == expected_answer

        logger.debug("Answer evaluation", correct=is_correct)

        points_available = int(question.get("points", 10))
        points_awarded = points_available if is_correct else 0

        return AnswerEvaluation(is_correct, points_awarded)

    def update_question_with_answer(self, question: dict, user_answer: str, is_correct: bool) -> None:
        """
        Update question dictionary with user answer and result

        Args:
            question: Question dictionary to update
            user_answer: User's submitted answer
            is_correct: Whether answer was correct

        Note:
            Modifies question dictionary in-place
        """
        question["user_answer"] = user_answer
        question["is_correct"] = is_correct
        question["timestamp"] = datetime.utcnow().isoformat()

    def calculate_session_completion(self, questions_answered: int, total_questions: int) -> bool:
        """
        Determine if session should be marked as completed

        Args:
            questions_answered: Number of questions answered
            total_questions: Total questions in session

        Returns:
            True if session should be completed
        """
        return questions_answered >= total_questions
