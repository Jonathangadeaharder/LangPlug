"""
Game Session Service

Handles game session lifecycle management including creation, retrieval, and updates.
Coordinates with GameQuestionService and GameScoringService.
"""

import json
import logging
import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import GameDifficulty, GameSessionStatus, GameType
from database.models import GameSession as GameSessionRecord

from .game_question_service import GameQuestion, GameQuestionService
from .game_scoring_service import GameScoringService

logger = logging.getLogger(__name__)


class GameSession(BaseModel):
    """Game session model"""

    session_id: str
    user_id: str
    game_type: GameType | str
    difficulty: GameDifficulty | str = GameDifficulty.INTERMEDIATE
    video_id: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    status: GameSessionStatus | str = GameSessionStatus.ACTIVE
    score: int = 0
    max_score: int = 100
    questions_answered: int = 0
    correct_answers: int = 0
    current_question: int = 0
    total_questions: int = 10
    session_data: dict = Field(default_factory=dict)


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


class AnswerResult(BaseModel):
    """Result of answer submission"""

    is_correct: bool
    points_earned: int
    current_score: int
    questions_remaining: int
    session_completed: bool


class GameSessionNotFoundError(Exception):
    """Raised when game session is not found"""

    pass


class GameSessionInactiveError(Exception):
    """Raised when attempting to modify inactive session"""

    pass


class QuestionNotFoundError(Exception):
    """Raised when question is not found in session"""

    pass


class QuestionAlreadyAnsweredError(Exception):
    """Raised when question has already been answered"""

    pass


class GameSessionService:
    """
    Service for managing game sessions

    Responsibilities:
        - Create new game sessions
        - Retrieve session data
        - Update session state after answers
        - Validate session access permissions
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.question_service = GameQuestionService()
        self.scoring_service = GameScoringService()

    async def create_session(self, user_id: str, request: StartGameRequest) -> GameSession:
        """
        Create a new game session

        Args:
            user_id: User creating the session
            request: Game configuration request

        Returns:
            Created GameSession

        Raises:
            Exception: If session creation fails
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        questions = await self.question_service.generate_questions(
            request.game_type, request.difficulty, request.video_id, request.total_questions
        )

        session_payload = {
            "questions": [q.model_dump() for q in questions],
            "created_at": now.isoformat(),
            "video_id": request.video_id,
        }

        record = GameSessionRecord(
            session_id=session_id,
            user_id=user_id,
            game_type=request.game_type.value,
            difficulty=request.difficulty.value,
            language="de",  # Default to German for now
            started_at=now,
            status=GameSessionStatus.ACTIVE.value,
            total_questions=request.total_questions,
            max_score=request.total_questions * 10,
            session_data=json.dumps(session_payload, ensure_ascii=False),
        )

        self.db_session.add(record)
        await self.db_session.commit()
        await self.db_session.refresh(record)

        logger.info(f"Created game session {session_id} for user {user_id}")
        return self._record_to_model(record)

    async def get_session(self, session_id: str, user_id: str) -> GameSession:
        """
        Get a game session by ID

        Args:
            session_id: Session identifier
            user_id: User requesting the session

        Returns:
            GameSession if found

        Raises:
            GameSessionNotFoundError: If session not found or access denied
        """
        result = await self.db_session.execute(
            select(GameSessionRecord).where(
                GameSessionRecord.session_id == session_id, GameSessionRecord.user_id == user_id
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            raise GameSessionNotFoundError(f"Game session {session_id} not found")

        return self._record_to_model(record)

    async def get_user_sessions(self, user_id: str, limit: int = 10) -> list[GameSession]:
        """
        Get user's game sessions

        Args:
            user_id: User identifier
            limit: Maximum sessions to return

        Returns:
            List of GameSession objects
        """
        result = await self.db_session.execute(
            select(GameSessionRecord)
            .where(GameSessionRecord.user_id == user_id)
            .order_by(GameSessionRecord.started_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()

        logger.info(f"Retrieved {len(records)} game sessions for user {user_id}")
        return [self._record_to_model(record) for record in records]

    async def submit_answer(self, user_id: str, answer_request: AnswerRequest) -> AnswerResult:
        """
        Submit an answer for a game question

        Args:
            user_id: User submitting the answer
            answer_request: Answer submission details

        Returns:
            AnswerResult with evaluation and updated scores

        Raises:
            GameSessionNotFoundError: If session not found
            GameSessionInactiveError: If session is not active
            QuestionNotFoundError: If question not found
            QuestionAlreadyAnsweredError: If question already answered
        """
        result = await self.db_session.execute(
            select(GameSessionRecord).where(
                GameSessionRecord.session_id == answer_request.session_id, GameSessionRecord.user_id == user_id
            )
        )
        record = result.scalar_one_or_none()

        self._validate_session(record)

        session_payload = self._deserialize_payload(record.session_data)
        question = self._find_question(session_payload, answer_request.question_id)

        evaluation = self.scoring_service.evaluate_answer(
            question, answer_request.user_answer, answer_request.correct_answer
        )

        self.scoring_service.update_question_with_answer(question, answer_request.user_answer, evaluation.is_correct)
        self._update_session_state(record, evaluation.is_correct, evaluation.points_awarded)

        record.session_data = json.dumps(session_payload, ensure_ascii=False)
        record.updated_at = datetime.utcnow()

        await self.db_session.commit()
        await self.db_session.refresh(record)

        logger.info(f"Answer submitted for session {answer_request.session_id} (correct={evaluation.is_correct})")

        return AnswerResult(
            is_correct=evaluation.is_correct,
            points_earned=evaluation.points_awarded,
            current_score=record.score,
            questions_remaining=max(record.total_questions - record.questions_answered, 0),
            session_completed=record.status == GameSessionStatus.COMPLETED.value,
        )

    def _validate_session(self, record: GameSessionRecord | None) -> None:
        """Validate session exists and is active"""
        if not record:
            raise GameSessionNotFoundError("Game session not found")
        if record.status != GameSessionStatus.ACTIVE.value:
            raise GameSessionInactiveError("Game session is not active")

    def _find_question(self, session_payload: dict, question_id: str) -> dict:
        """Find question in session by ID"""
        questions = session_payload.get("questions", [])
        question = next((q for q in questions if q.get("question_id") == question_id), None)

        if not question:
            raise QuestionNotFoundError(f"Question {question_id} not found")
        if question.get("user_answer") is not None:
            raise QuestionAlreadyAnsweredError(f"Question {question_id} already answered")

        return question

    def _update_session_state(self, record: GameSessionRecord, is_correct: bool, points_awarded: int) -> None:
        """Update session state after answer submission"""
        record.questions_answered += 1
        record.current_question = min(record.current_question + 1, record.total_questions)

        if is_correct:
            record.correct_answers += 1
            record.score += points_awarded

        if self.scoring_service.calculate_session_completion(record.questions_answered, record.total_questions):
            record.status = GameSessionStatus.COMPLETED.value
            record.completed_at = datetime.utcnow()

    def _deserialize_payload(self, raw: str | None) -> dict:
        """Deserialize session payload from JSON"""
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            logger.warning("Failed to decode stored game session payload", exc_info=True)
        return {}

    def _record_to_model(self, record: GameSessionRecord) -> GameSession:
        """Convert database record to GameSession model"""
        session_payload = self._deserialize_payload(record.session_data)
        return GameSession(
            session_id=record.session_id,
            user_id=str(record.user_id),
            game_type=record.game_type,
            difficulty=record.difficulty,
            video_id=session_payload.get("video_id"),
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
