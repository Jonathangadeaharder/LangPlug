"""Game session management API routes"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import current_active_user
from database.models import GameSession as GameSessionRecord
from database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["game"])


class GameSession(BaseModel):
    """Game session model"""

    session_id: str
    user_id: str
    game_type: str  # "vocabulary", "listening", "comprehension"
    difficulty: str = "intermediate"  # "beginner", "intermediate", "advanced"
    video_id: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "active"  # "active", "completed", "paused", "abandoned"
    score: int = 0
    max_score: int = 100
    questions_answered: int = 0
    correct_answers: int = 0
    current_question: int = 0
    total_questions: int = 10
    session_data: dict[str, Any] = Field(default_factory=dict)


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
    timestamp: datetime | None = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Question text cannot be empty")
        return v


class GameType(str, Enum):
    """Valid game types"""

    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    COMPREHENSION = "comprehension"


class GameDifficulty(str, Enum):
    """Valid difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StartGameRequest(BaseModel):
    """Request model for starting a game session"""

    game_type: GameType
    difficulty: GameDifficulty = GameDifficulty.INTERMEDIATE
    video_id: str | None = None
    total_questions: int = Field(default=10, ge=1, le=50)


class AnswerRequest(BaseModel):
    """Request model for submitting an answer"""

    session_id: str
    question_id: str
    question_type: str = "multiple_choice"
    user_answer: str
    correct_answer: str | None = None
    points: int = 10


def _deserialize_session_payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        logger.warning("Failed to decode stored game session payload", exc_info=True)
    return {}


def _record_to_game_session(record: GameSessionRecord) -> GameSession:
    session_payload = _deserialize_session_payload(record.session_data)
    return GameSession(
        session_id=record.session_id,
        user_id=str(record.user_id),
        game_type=record.game_type,
        difficulty=record.difficulty,
        video_id=session_payload.get("video_id"),  # Extract from session_data
        started_at=record.started_at,
        completed_at=record.completed_at,
        status=record.status,
        score=record.score,
        max_score=record.max_score,
        questions_answered=record.questions_answered,
        correct_answers=record.correct_answers,
        current_question=record.current_question,
        total_questions=record.total_questions,
        session_data=session_payload,
    )


@router.post("/start", response_model=GameSession, name="game_start_session")
async def start_game_session(
    game_request: StartGameRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Start a new vocabulary game session for the current user.

    Creates a new game session with generated questions based on game type and difficulty.
    Supports vocabulary translation, listening comprehension, and general comprehension games.

    **Authentication Required**: Yes

    Args:
        game_request (StartGameRequest): Game configuration with:
            - game_type (GameType): "vocabulary", "listening", or "comprehension"
            - difficulty (GameDifficulty): "beginner", "intermediate", or "advanced"
            - video_id (str, optional): Associated video for context
            - total_questions (int): Number of questions (1-50, default: 10)
        current_user (User): Authenticated user
        db (AsyncSession): Database session

    Returns:
        GameSession: Created game session with:
            - session_id: Unique session identifier
            - game_type: Type of game
            - difficulty: Difficulty level
            - total_questions: Number of questions
            - status: "active"
            - session_data: Generated questions

    Raises:
        HTTPException: 500 if session creation fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/game/start" \
          -H "Authorization: Bearer <token>" \
          -H "Content-Type: application/json" \
          -d '{
            "game_type": "vocabulary",
            "difficulty": "intermediate",
            "total_questions": 15
          }'
        ```

        Response:
        ```json
        {
            "session_id": "abc-123-def",
            "user_id": "user-456",
            "game_type": "vocabulary",
            "difficulty": "intermediate",
            "status": "active",
            "total_questions": 15,
            "current_question": 0,
            "score": 0,
            "max_score": 150
        }
        ```
    """
    try:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        questions = await generate_game_questions(
            game_request.game_type,
            game_request.difficulty,
            game_request.video_id,
            game_request.total_questions,
        )

        session_payload = {
            "questions": [q.model_dump() for q in questions],
            "created_at": now.isoformat(),
            "video_id": game_request.video_id,
        }

        record = GameSessionRecord(
            session_id=session_id,
            user_id=str(current_user.id),
            game_type=game_request.game_type.value,
            difficulty=game_request.difficulty.value,
            language="de",  # Default to German for now
            started_at=now,
            status="active",
            total_questions=game_request.total_questions,
            max_score=game_request.total_questions * 10,
            session_data=json.dumps(session_payload, ensure_ascii=False),
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)

        logger.info("Started game session %s for user %s", session_id, current_user.id)
        return _record_to_game_session(record)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error starting game session: %s", exc, exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error starting game session: {exc!s}") from exc


@router.get("/session/{session_id}", response_model=GameSession, name="game_get_session")
async def get_game_session(
    session_id: str,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific game session"""
    try:
        result = await db.execute(
            select(GameSessionRecord).where(
                GameSessionRecord.session_id == session_id,
                GameSessionRecord.user_id == str(current_user.id),
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Game session not found")

        return _record_to_game_session(record)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error getting game session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game session: {exc!s}") from exc


def _validate_game_session(record: GameSessionRecord | None) -> None:
    """Validate game session exists and is active"""
    if not record:
        raise HTTPException(status_code=404, detail="Game session not found")
    if record.status != "active":
        raise HTTPException(status_code=400, detail="Game session is not active")


def _find_question(session_payload: dict, question_id: str) -> dict:
    """Find question in session by ID"""
    questions = session_payload.get("questions", [])
    question = next((q for q in questions if q.get("question_id") == question_id), None)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.get("user_answer") is not None:
        raise HTTPException(status_code=400, detail="Question already answered")

    return question


def _evaluate_answer(question: dict, answer_request: AnswerRequest) -> tuple[bool, int]:
    """Evaluate user answer and calculate points"""
    expected_answer = (question.get("correct_answer") or answer_request.correct_answer or "").strip().lower()
    user_answer = answer_request.user_answer.strip().lower()
    is_correct = expected_answer and user_answer == expected_answer

    logger.info(f"Question correct_answer: {question.get('correct_answer')}")
    logger.info(f"Request correct_answer: {answer_request.correct_answer}")
    logger.info(f"Expected answer: '{expected_answer}'")
    logger.info(f"User answer: '{user_answer}'")
    logger.info(f"Is correct: {is_correct}")

    points_available = int(question.get("points") or answer_request.points or 0)
    points_awarded = points_available if is_correct else 0

    return is_correct, points_awarded


def _update_question_data(question: dict, answer_request: AnswerRequest, is_correct: bool) -> None:
    """Update question with user answer and result"""
    question["user_answer"] = answer_request.user_answer
    question["is_correct"] = is_correct
    question["timestamp"] = datetime.utcnow().isoformat()


def _update_session_state(record: GameSessionRecord, is_correct: bool, points_awarded: int) -> None:
    """Update session state after answer submission"""
    record.questions_answered += 1
    record.current_question = min(record.current_question + 1, record.total_questions)

    if is_correct:
        record.correct_answers += 1
        record.score += points_awarded

    if record.questions_answered >= record.total_questions:
        record.status = "completed"
        record.completed_at = datetime.utcnow()


def _create_answer_result(record: GameSessionRecord, is_correct: bool, points_awarded: int) -> dict:
    """Create answer submission result payload"""
    return {
        "is_correct": is_correct,
        "points_earned": points_awarded,
        "current_score": record.score,
        "questions_remaining": max(record.total_questions - record.questions_answered, 0),
        "session_completed": record.status == "completed",
    }


@router.post("/answer", name="game_submit_answer")
async def submit_answer(
    answer_request: AnswerRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Submit an answer for a game question and receive immediate feedback.

    Evaluates the user's answer against the correct answer, updates score, and
    automatically completes the session when all questions are answered.

    **Authentication Required**: Yes

    Args:
        answer_request (AnswerRequest): Answer submission with:
            - session_id (str): Game session identifier
            - question_id (str): Question identifier
            - user_answer (str): User's submitted answer
            - correct_answer (str, optional): Expected correct answer
            - points (int): Points available for this question
        current_user (User): Authenticated user
        db (AsyncSession): Database session

    Returns:
        dict: Answer result with:
            - is_correct: Whether answer was correct
            - points_earned: Points awarded
            - current_score: Updated total score
            - questions_remaining: Remaining questions
            - session_completed: Whether session is finished

    Raises:
        HTTPException: 404 if session or question not found
        HTTPException: 400 if question already answered or session not active
        HTTPException: 500 if answer processing fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/game/answer" \
          -H "Authorization: Bearer <token>" \
          -H "Content-Type: application/json" \
          -d '{
            "session_id": "abc-123",
            "question_id": "q1",
            "user_answer": "hola",
            "points": 10
          }'
        ```

        Response:
        ```json
        {
            "is_correct": true,
            "points_earned": 10,
            "current_score": 10,
            "questions_remaining": 9,
            "session_completed": false
        }
        ```
    """
    try:
        result = await db.execute(
            select(GameSessionRecord).where(
                GameSessionRecord.session_id == answer_request.session_id,
                GameSessionRecord.user_id == str(current_user.id),
            )
        )
        record = result.scalar_one_or_none()

        _validate_game_session(record)

        session_payload = _deserialize_session_payload(record.session_data)
        question = _find_question(session_payload, answer_request.question_id)

        is_correct, points_awarded = _evaluate_answer(question, answer_request)
        _update_question_data(question, answer_request, is_correct)
        _update_session_state(record, is_correct, points_awarded)

        record.session_data = json.dumps(session_payload, ensure_ascii=False)
        record.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(record)

        logger.info("Answer submitted for session %s (correct=%s)", answer_request.session_id, is_correct)
        return _create_answer_result(record, is_correct, points_awarded)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error submitting answer: %s", exc, exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {exc!s}") from exc


@router.get("/sessions", response_model=list[GameSession], name="game_get_user_sessions")
async def get_user_game_sessions(
    limit: int = 10,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get user's game sessions"""
    try:
        result = await db.execute(
            select(GameSessionRecord)
            .where(GameSessionRecord.user_id == str(current_user.id))
            .order_by(GameSessionRecord.started_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()

        logger.info("Retrieved %s game sessions for user %s", len(records), current_user.id)
        return [_record_to_game_session(record) for record in records]

    except Exception as exc:
        logger.error("Error getting user game sessions: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game sessions: {exc!s}") from exc


def _normalize_enum_values(game_type: str | GameType, difficulty: str | GameDifficulty) -> tuple[str, str]:
    """Normalize enum values to strings"""
    if isinstance(game_type, GameType):
        game_type = game_type.value
    if isinstance(difficulty, GameDifficulty):
        difficulty = difficulty.value
    return game_type, difficulty


def _generate_vocabulary_questions(difficulty: str, total_questions: int) -> list[GameQuestion]:
    """Generate vocabulary translation questions"""
    sample_words = [
        {"word": "hello", "translation": "hola", "difficulty": "beginner"},
        {"word": "goodbye", "translation": "adiós", "difficulty": "beginner"},
        {"word": "beautiful", "translation": "hermoso", "difficulty": "intermediate"},
        {"word": "complicated", "translation": "complicado", "difficulty": "advanced"},
        {"word": "understand", "translation": "entender", "difficulty": "intermediate"},
    ]

    filtered_words = [w for w in sample_words if w["difficulty"] == difficulty]
    if not filtered_words:
        filtered_words = sample_words

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

    return questions


def _generate_listening_questions(total_questions: int) -> list[GameQuestion]:
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
    return questions


def _generate_comprehension_questions(total_questions: int) -> list[GameQuestion]:
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
    return questions


async def generate_game_questions(
    game_type: str | GameType, difficulty: str | GameDifficulty, video_id: str | None, total_questions: int
) -> list[GameQuestion]:
    """Generate questions for a game session (Refactored for lower complexity)"""
    game_type, difficulty = _normalize_enum_values(game_type, difficulty)

    if game_type == "vocabulary":
        return _generate_vocabulary_questions(difficulty, total_questions)
    elif game_type == "listening":
        return _generate_listening_questions(total_questions)
    else:  # comprehension
        return _generate_comprehension_questions(total_questions)
