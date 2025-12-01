"""
Game session management API routes

Thin API layer delegating to GameSessionService, GameQuestionService, and GameScoringService.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger
from core.database import get_async_session
from core.dependencies import current_active_user
from database.models import User
from services.gameservice import GameSessionService
from services.gameservice.game_question_service import GameQuestionService
from services.gameservice.game_scoring_service import GameScoringService
from services.gameservice.game_session_service import (
    AnswerRequest,
    GameSession,
    GameSessionInactiveError,
    GameSessionNotFoundError,
    QuestionAlreadyAnsweredError,
    QuestionNotFoundError,
    StartGameRequest,
)

logger = get_logger(__name__)

router = APIRouter(tags=["game"])


def _get_game_service(
    db: AsyncSession = Depends(get_async_session),
) -> GameSessionService:
    """Dependency for GameSessionService"""
    question_service = GameQuestionService(db)
    scoring_service = GameScoringService()
    return GameSessionService(db, question_service, scoring_service)


@router.post("/start", response_model=GameSession, name="game_start_session")
async def start_game_session(
    game_request: StartGameRequest,
    current_user: User = Depends(current_active_user),
    game_service: GameSessionService = Depends(_get_game_service),
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
        game_service (GameSessionService): Game session service

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
        session = await game_service.create_session(str(current_user.id), game_request)
        return session

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error starting game session", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting game session: {exc!s}") from exc


@router.get("/session/{session_id}", response_model=GameSession, name="game_get_session")
async def get_game_session(
    session_id: str,
    current_user: User = Depends(current_active_user),
    game_service: GameSessionService = Depends(_get_game_service),
):
    """
    Get a specific game session

    Args:
        session_id: Game session identifier
        current_user: Authenticated user
        game_service: Game session service

    Returns:
        GameSession if found

    Raises:
        HTTPException: 404 if session not found
        HTTPException: 500 if retrieval fails
    """
    try:
        session = await game_service.get_session(session_id, str(current_user.id))
        return session

    except GameSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error getting game session", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game session: {exc!s}") from exc


@router.post("/answer", name="game_submit_answer")
async def submit_answer(
    answer_request: AnswerRequest,
    current_user: User = Depends(current_active_user),
    game_service: GameSessionService = Depends(_get_game_service),
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
        game_service (GameSessionService): Game session service

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
        result = await game_service.submit_answer(str(current_user.id), answer_request)
        return result.model_dump()

    except GameSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GameSessionInactiveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except QuestionAlreadyAnsweredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error submitting answer", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {exc!s}") from exc


@router.get("/sessions", response_model=list[GameSession], name="game_get_user_sessions")
async def get_user_game_sessions(
    limit: int = 10,
    current_user: User = Depends(current_active_user),
    game_service: GameSessionService = Depends(_get_game_service),
):
    """
    Get user's game sessions

    Args:
        limit: Maximum number of sessions to return
        current_user: Authenticated user
        game_service: Game session service

    Returns:
        List of GameSession objects

    Raises:
        HTTPException: 500 if retrieval fails
    """
    try:
        sessions = await game_service.get_user_sessions(str(current_user.id), limit)
        return sessions

    except Exception as exc:
        logger.error("Error getting user game sessions", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game sessions: {exc!s}") from exc
