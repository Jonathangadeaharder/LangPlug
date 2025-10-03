"""
Game Question Service

Handles generation of game questions for different game types and difficulty levels.
Isolated from session management and scoring logic.
"""

import logging

from pydantic import BaseModel, field_validator

from core.enums import GameDifficulty, GameType

logger = logging.getLogger(__name__)


class GameQuestion(BaseModel):
    """Game question model"""

    question_id: str
    question_type: str  # "multiple_choice", "fill_blank", "translation"
    question_text: str
    options: list[str] | None = None
    correct_answer: str
    user_answer: str | None = None
    is_correct: bool | None = None
    points: int = 10
    timestamp: str | None = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v


class GameQuestionService:
    """
    Service for generating game questions

    Responsibilities:
        - Generate questions for different game types
        - Filter questions by difficulty level
        - Provide question templates and samples
    """

    def __init__(self):
        self._sample_vocabulary = [
            {"word": "hello", "translation": "hola", "difficulty": "beginner"},
            {"word": "goodbye", "translation": "adiós", "difficulty": "beginner"},
            {"word": "beautiful", "translation": "hermoso", "difficulty": "intermediate"},
            {"word": "complicated", "translation": "complicado", "difficulty": "advanced"},
            {"word": "understand", "translation": "entender", "difficulty": "intermediate"},
        ]

    async def generate_questions(
        self, game_type: str | GameType, difficulty: str | GameDifficulty, video_id: str | None, total_questions: int
    ) -> list[GameQuestion]:
        """
        Generate questions for a game session

        Args:
            game_type: Type of game (vocabulary, listening, comprehension)
            difficulty: Difficulty level (beginner, intermediate, advanced)
            video_id: Optional video context for questions
            total_questions: Number of questions to generate

        Returns:
            List of GameQuestion objects
        """
        game_type_str, difficulty_str = self._normalize_enum_values(game_type, difficulty)

        if game_type_str == "vocabulary":
            return self._generate_vocabulary_questions(difficulty_str, total_questions)
        elif game_type_str == "listening":
            return self._generate_listening_questions(total_questions)
        else:  # comprehension
            return self._generate_comprehension_questions(total_questions)

    def _normalize_enum_values(self, game_type: str | GameType, difficulty: str | GameDifficulty) -> tuple[str, str]:
        """Normalize enum values to strings"""
        if isinstance(game_type, GameType):
            game_type = game_type.value
        if isinstance(difficulty, GameDifficulty):
            difficulty = difficulty.value
        return game_type, difficulty

    def _generate_vocabulary_questions(self, difficulty: str, total_questions: int) -> list[GameQuestion]:
        """Generate vocabulary translation questions"""
        filtered_words = [w for w in self._sample_vocabulary if w["difficulty"] == difficulty]
        if not filtered_words:
            filtered_words = self._sample_vocabulary

        questions = []
        for i in range(total_questions):
            word_data = filtered_words[i % len(filtered_words)]
            question = GameQuestion(
                question_id=f"q{i + 1}",
                question_type="translation",
                question_text=f"What is the translation of '{word_data['word']}'?",
                correct_answer=word_data["translation"],
                points=10,
            )
            questions.append(question)

        logger.info(f"Generated {len(questions)} vocabulary questions (difficulty={difficulty})")
        return questions

    def _generate_listening_questions(self, total_questions: int) -> list[GameQuestion]:
        """Generate listening comprehension questions"""
        questions = []
        for i in range(total_questions):
            question = GameQuestion(
                question_id=f"q{i + 1}",
                question_type="multiple_choice",
                question_text=f"What did the speaker say in segment {i + 1}?",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                points=10,
            )
            questions.append(question)

        logger.info(f"Generated {len(questions)} listening questions")
        return questions

    def _generate_comprehension_questions(self, total_questions: int) -> list[GameQuestion]:
        """Generate comprehension questions"""
        questions = []
        for i in range(total_questions):
            question = GameQuestion(
                question_id=f"q{i + 1}",
                question_type="multiple_choice",
                question_text=f"What was the main idea of segment {i + 1}?",
                options=["Idea A", "Idea B", "Idea C", "Idea D"],
                correct_answer="Idea A",
                points=10,
            )
            questions.append(question)

        logger.info(f"Generated {len(questions)} comprehension questions")
        return questions
