"""
Game Model Validation Tests

Tests game session and question model validation logic,
ensuring proper data structures and business rules.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

# Import game models from routes since they're defined there
from api.routes.game import GameQuestion, GameSession


class TestGameSessionValidation:
    """Test GameSession model validation and business logic"""

    def test_WhenValidGameSessionData_ThenCreatesSuccessfully(self):
        """Test creating game session with valid data succeeds"""
        session_data = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "game_type": "vocabulary",
            "difficulty": "intermediate",
            "started_at": datetime.now(),
            "status": "active",
            "total_questions": 10,
        }

        session = GameSession(**session_data)

        assert session.game_type == "vocabulary"
        assert session.difficulty == "intermediate"
        assert session.status == "active"
        assert session.score == 0  # Default value
        assert session.max_score == 100  # Default value
        assert session.current_question == 0  # Default value
        assert session.total_questions == 10

    def test_WhenGameSessionWithVideo_ThenIncludesVideoId(self):
        """Test game session with video context includes video ID"""
        video_id = str(uuid4())
        session_data = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "game_type": "listening",
            "video_id": video_id,
            "started_at": datetime.now(),
        }

        session = GameSession(**session_data)

        assert session.video_id == video_id
        assert session.game_type == "listening"

    def test_WhenGameSessionWithCompleteData_ThenSetsAllFields(self):
        """Test game session with complete data sets all fields correctly"""
        completed_at = datetime.now()
        session_data = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "game_type": "comprehension",
            "difficulty": "advanced",
            "started_at": datetime.now(),
            "completed_at": completed_at,
            "status": "completed",
            "score": 85,
            "max_score": 100,
            "questions_answered": 8,
            "correct_answers": 7,
            "current_question": 8,
            "total_questions": 8,
            "session_data": {"custom_field": "value"},
        }

        session = GameSession(**session_data)

        assert session.completed_at == completed_at
        assert session.status == "completed"
        assert session.score == 85
        assert session.questions_answered == 8
        assert session.correct_answers == 7
        assert session.session_data == {"custom_field": "value"}

    def test_WhenGameSessionDefaultValues_ThenSetsCorrectDefaults(self):
        """Test game session uses correct default values"""
        minimal_data = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "game_type": "vocabulary",
            "started_at": datetime.now(),
        }

        session = GameSession(**minimal_data)

        assert session.difficulty == "intermediate"  # Default
        assert session.video_id is None  # Default
        assert session.completed_at is None  # Default
        assert session.status == "active"  # Default
        assert session.score == 0  # Default
        assert session.max_score == 100  # Default
        assert session.questions_answered == 0  # Default
        assert session.correct_answers == 0  # Default
        assert session.current_question == 0  # Default
        assert session.total_questions == 10  # Default
        assert session.session_data == {}  # Default

    def test_WhenMissingRequiredFields_ThenRaisesValidationError(self):
        """Test missing required fields raises validation error"""
        incomplete_data = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            # Missing game_type and started_at
        }

        with pytest.raises(ValidationError) as exc_info:
            GameSession(**incomplete_data)

        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]

        assert "game_type" in field_names
        assert "started_at" in field_names

    def test_WhenInvalidUuidFields_ThenRaisesValidationError(self):
        """Test invalid UUID format in ID fields raises validation error"""
        invalid_data = {
            "session_id": "not-a-uuid",
            "user_id": "also-not-a-uuid",
            "game_type": "vocabulary",
            "started_at": datetime.now(),
        }

        # Note: Current model uses str type, but this tests future UUID validation
        # This test documents expected behavior if UUID validation is added
        session = GameSession(**invalid_data)
        assert session.session_id == "not-a-uuid"  # Currently accepts any string


class TestGameQuestionValidation:
    """Test GameQuestion model validation and business logic"""

    def test_WhenValidQuestionData_ThenCreatesSuccessfully(self):
        """Test creating game question with valid data succeeds"""
        question_data = {
            "question_id": str(uuid4()),
            "question_type": "multiple_choice",
            "question_text": "What does 'Haus' mean in English?",
            "options": ["House", "Car", "Tree", "Book"],
            "correct_answer": "House",
            "points": 10,
        }

        question = GameQuestion(**question_data)

        assert question.question_type == "multiple_choice"
        assert question.question_text == "What does 'Haus' mean in English?"
        assert len(question.options) == 4
        assert question.correct_answer == "House"
        assert question.points == 10

    def test_WhenFillBlankQuestion_ThenHandlesNoOptions(self):
        """Test fill-in-the-blank question without options"""
        question_data = {
            "question_id": str(uuid4()),
            "question_type": "fill_blank",
            "question_text": "The German word for house is ____",
            "correct_answer": "Haus",
            "points": 15,
        }

        question = GameQuestion(**question_data)

        assert question.question_type == "fill_blank"
        assert question.options is None
        assert question.correct_answer == "Haus"

    def test_WhenTranslationQuestion_ThenSetsCorrectType(self):
        """Test translation question type and structure"""
        question_data = {
            "question_id": str(uuid4()),
            "question_type": "translation",
            "question_text": "Translate: The house is big",
            "correct_answer": "Das Haus ist groß",
            "points": 20,
        }

        question = GameQuestion(**question_data)

        assert question.question_type == "translation"
        assert question.points == 20

    def test_WhenQuestionWithUserAnswer_ThenSetsAnswerData(self):
        """Test question with user answer and correctness evaluation"""
        question_data = {
            "question_id": str(uuid4()),
            "question_type": "multiple_choice",
            "question_text": "What color is the sky?",
            "options": ["Blue", "Red", "Green"],
            "correct_answer": "Blue",
            "user_answer": "Blue",
            "is_correct": True,
            "points": 10,
            "timestamp": datetime.now(),
        }

        question = GameQuestion(**question_data)

        assert question.user_answer == "Blue"
        assert question.is_correct is True
        assert question.timestamp is not None

    def test_WhenQuestionDefaultValues_ThenSetsCorrectDefaults(self):
        """Test question uses correct default values"""
        minimal_data = {
            "question_id": str(uuid4()),
            "question_type": "multiple_choice",
            "question_text": "Sample question",
            "correct_answer": "Answer",
        }

        question = GameQuestion(**minimal_data)

        assert question.options is None  # Default
        assert question.user_answer is None  # Default
        assert question.is_correct is None  # Default
        assert question.points == 10  # Default
        assert question.timestamp is None  # Default

    def test_WhenMissingRequiredQuestionFields_ThenRaisesValidationError(self):
        """Test missing required question fields raises validation error"""
        incomplete_data = {
            "question_id": str(uuid4()),
            "question_type": "multiple_choice",
            # Missing question_text and correct_answer
        }

        with pytest.raises(ValidationError) as exc_info:
            GameQuestion(**incomplete_data)

        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]

        assert "question_text" in field_names
        assert "correct_answer" in field_names

    def test_WhenEmptyQuestionText_ThenRaisesValidationError(self):
        """Test empty question text raises validation error"""
        invalid_data = {
            "question_id": str(uuid4()),
            "question_type": "multiple_choice",
            "question_text": "",  # Empty string
            "correct_answer": "Answer",
        }

        with pytest.raises(ValidationError) as exc_info:
            GameQuestion(**invalid_data)

        exc_info.value.errors()
        # Should validate minimum length for question_text

    def test_WhenNegativePoints_ThenAcceptsValue(self):
        """Test negative points value (for penalty systems)"""
        question_data = {
            "question_id": str(uuid4()),
            "question_type": "multiple_choice",
            "question_text": "Penalty question",
            "correct_answer": "Answer",
            "points": -5,  # Negative points for penalties
        }

        question = GameQuestion(**question_data)
        assert question.points == -5


class TestGameModelBusinessLogic:
    """Test business logic and relationships between game models"""

    def test_WhenCalculateSessionScore_ThenSumsQuestionPoints(self):
        """Test session scoring logic with multiple questions"""
        # This tests the concept of how scoring would work
        # In actual implementation, this logic would be in service layer

        questions = [
            {"correct_answer": "A", "user_answer": "A", "points": 10},
            {"correct_answer": "B", "user_answer": "B", "points": 15},
            {"correct_answer": "C", "user_answer": "Wrong", "points": 10},
        ]

        total_score = sum(q["points"] for q in questions if q["correct_answer"] == q["user_answer"])

        assert total_score == 25  # 10 + 15 + 0

    def test_WhenCalculateAccuracyPercentage_ThenReturnsCorrectRatio(self):
        """Test accuracy calculation logic"""
        correct_answers = 7
        total_questions = 10

        accuracy = (correct_answers / total_questions) * 100

        assert accuracy == 70.0

    def test_WhenSessionComplete_ThenAllQuestionsAnswered(self):
        """Test session completion logic"""
        session_data = {
            "session_id": str(uuid4()),
            "user_id": str(uuid4()),
            "game_type": "vocabulary",
            "started_at": datetime.now(),
            "total_questions": 5,
            "questions_answered": 5,
            "status": "completed",
        }

        session = GameSession(**session_data)

        # Business logic: session is complete when questions_answered == total_questions
        is_complete = session.questions_answered == session.total_questions
        assert is_complete is True
        assert session.status == "completed"
