"""
Quiz API Routes

Endpoints for vocabulary quiz generation and spaced repetition review.
Based on SM-2 algorithm research and Vocabulary Builder patterns.
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import current_active_user
from database.models import User
from services.learning.quiz_generator import QuizGenerator, QuizType, QuizQuestion, QuizSession
from services.learning.spaced_repetition import ReviewQuality

logger = logging.getLogger(__name__)
router = APIRouter(tags=["quiz"])


# In-memory storage for quiz sessions (replace with Redis/DB in production)
_quiz_sessions: dict[str, QuizSession] = {}


class StartQuizRequest(BaseModel):
    """Request to start a new quiz session"""
    num_questions: int = Field(10, ge=1, le=50, description="Number of questions")
    quiz_types: list[str] | None = Field(None, description="Question types to include")
    difficulty_filter: str | None = Field(None, description="CEFR level filter (A1, A2, etc.)")


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer"""
    question_id: str = Field(..., description="Question identifier")
    user_answer: str = Field(..., description="User's answer")
    quality: int = Field(..., ge=0, le=5, description="Self-assessed recall quality (0-5)")


class QuizQuestionResponse(BaseModel):
    """Quiz question response"""
    question_id: str
    question_type: str
    word: str
    options: list[str]
    hint: str | None = None
    context_sentence: str | None = None


class QuizSessionResponse(BaseModel):
    """Quiz session response"""
    session_id: str
    total_questions: int
    current_question: int
    question: QuizQuestionResponse | None = None
    completed: bool = False


class QuizResultResponse(BaseModel):
    """Quiz result response"""
    session_id: str
    score: int
    total_questions: int
    percentage: float
    time_taken: str
    words_reviewed: list[str]


@router.post("/quiz/start", name="start_quiz_session")
async def start_quiz_session(
    request: StartQuizRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> QuizSessionResponse:
    """
    Start a new quiz session with spaced repetition.

    Generates questions based on SM-2 algorithm, prioritizing:
    - Due vocabulary items (past review date)
    - Difficult words (low easiness factor)
    - Recently encountered words

    **Authentication Required**: Yes

    Args:
        request: Quiz configuration with:
            - num_questions: Number of questions (1-50, default: 10)
            - quiz_types: Question types (default: ["multiple_choice", "fill_blank"])
            - difficulty_filter: Optional CEFR level (A1, A2, B1, B2, C1, C2)
        current_user: Authenticated user
        db: Database session

    Returns:
        QuizSessionResponse with first question

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/quiz/start \
          -H "Authorization: Bearer $TOKEN" \
          -d '{
            "num_questions": 15,
            "quiz_types": ["multiple_choice", "fill_blank"],
            "difficulty_filter": "A2"
          }'
        ```

        Response:
        ```json
        {
          "session_id": "quiz_123_abc456",
          "total_questions": 15,
          "current_question": 1,
          "question": {
            "question_id": "q_abc123",
            "question_type": "multiple_choice",
            "word": "Hund",
            "options": ["dog", "cat", "bird", "fish"],
            "hint": "What is the English translation of 'Hund'?"
          },
          "completed": false
        }
        ```
    """
    try:
        # Parse quiz types
        quiz_types_enum = None
        if request.quiz_types:
            try:
                quiz_types_enum = [QuizType(qt) for qt in request.quiz_types]
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid quiz type. Valid types: {[qt.value for qt in QuizType]}"
                )

        # Generate quiz session
        generator = QuizGenerator(db)
        session = await generator.generate_quiz_session(
            user_id=current_user.id,
            num_questions=request.num_questions,
            quiz_types=quiz_types_enum,
            difficulty_filter=request.difficulty_filter
        )

        # Store session
        _quiz_sessions[session.session_id] = session

        logger.info(f"Started quiz session {session.session_id} for user {current_user.id}")

        # Return first question
        if session.questions:
            first_question = session.questions[0]
            return QuizSessionResponse(
                session_id=session.session_id,
                total_questions=session.total_questions,
                current_question=1,
                question=QuizQuestionResponse(
                    question_id=first_question.question_id,
                    question_type=first_question.question_type.value,
                    word=first_question.word,
                    options=first_question.options,
                    hint=first_question.hint,
                    context_sentence=first_question.context_sentence
                ),
                completed=False
            )
        else:
            raise HTTPException(
                status_code=422,
                detail="No vocabulary available for quiz. Please add some words first."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start quiz session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start quiz: {str(e)}"
        ) from e


@router.post("/quiz/{session_id}/answer", name="submit_quiz_answer")
async def submit_quiz_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> QuizSessionResponse:
    """
    Submit answer and get next question.

    Records answer correctness and updates spaced repetition schedule
    based on user's self-assessed recall quality.

    **Authentication Required**: Yes

    Args:
        session_id: Quiz session identifier
        request: Answer submission with:
            - question_id: Question being answered
            - user_answer: User's answer
            - quality: Self-assessed recall quality (0-5)
                - 0: Complete blackout
                - 1: Incorrect, seemed easy
                - 2: Incorrect, difficult
                - 3: Correct with difficulty
                - 4: Correct after hesitation
                - 5: Perfect recall
        current_user: Authenticated user
        db: Database session

    Returns:
        QuizSessionResponse with next question or completion status

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/quiz/quiz_123_abc456/answer \
          -H "Authorization: Bearer $TOKEN" \
          -d '{
            "question_id": "q_abc123",
            "user_answer": "dog",
            "quality": 5
          }'
        ```

        Response (next question):
        ```json
        {
          "session_id": "quiz_123_abc456",
          "total_questions": 15,
          "current_question": 2,
          "question": {
            "question_id": "q_def456",
            "question_type": "fill_blank",
            "word": "Katze",
            "options": [],
            "hint": "Type the English translation",
            "context_sentence": "'Katze' means ______"
          },
          "completed": false
        }
        ```

        Response (completed):
        ```json
        {
          "session_id": "quiz_123_abc456",
          "total_questions": 15,
          "current_question": 15,
          "question": null,
          "completed": true
        }
        ```
    """
    # Get session
    session = _quiz_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    # Verify user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this quiz")

    # Find the question
    question = next(
        (q for q in session.questions if q.question_id == request.question_id),
        None
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found in session")

    # Check answer
    is_correct = question.check_answer(request.user_answer)

    if is_correct:
        session.score += 1

    # Update spaced repetition schedule
    try:
        await _update_spaced_repetition(
            user_id=current_user.id,
            word=question.word,
            quality=ReviewQuality(request.quality),
            db=db
        )
    except Exception as e:
        logger.error(f"Failed to update spaced repetition: {e}")
        # Continue even if SR update fails

    # Find current question index
    current_index = next(
        (i for i, q in enumerate(session.questions) if q.question_id == request.question_id),
        -1
    )

    # Check if there are more questions
    if current_index + 1 < len(session.questions):
        # Return next question
        next_question = session.questions[current_index + 1]
        return QuizSessionResponse(
            session_id=session.session_id,
            total_questions=session.total_questions,
            current_question=current_index + 2,
            question=QuizQuestionResponse(
                question_id=next_question.question_id,
                question_type=next_question.question_type.value,
                word=next_question.word,
                options=next_question.options,
                hint=next_question.hint,
                context_sentence=next_question.context_sentence
            ),
            completed=False
        )
    else:
        # Quiz completed
        session.completed_at = datetime.now().isoformat()

        return QuizSessionResponse(
            session_id=session.session_id,
            total_questions=session.total_questions,
            current_question=len(session.questions),
            question=None,
            completed=True
        )


@router.get("/quiz/{session_id}/result", name="get_quiz_result")
async def get_quiz_result(
    session_id: str,
    current_user: User = Depends(current_active_user),
) -> QuizResultResponse:
    """
    Get quiz results after completion.

    **Authentication Required**: Yes

    Args:
        session_id: Quiz session identifier
        current_user: Authenticated user

    Returns:
        QuizResultResponse with score and statistics

    Example:
        ```bash
        curl http://localhost:8000/api/quiz/quiz_123_abc456/result \
          -H "Authorization: Bearer $TOKEN"
        ```

        Response:
        ```json
        {
          "session_id": "quiz_123_abc456",
          "score": 12,
          "total_questions": 15,
          "percentage": 80.0,
          "time_taken": "3m 45s",
          "words_reviewed": ["Hund", "Katze", "Haus", ...]
        }
        ```
    """
    # Get session
    session = _quiz_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    # Verify user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this quiz")

    # Calculate time taken
    if session.completed_at:
        started = datetime.fromisoformat(session.started_at)
        completed = datetime.fromisoformat(session.completed_at)
        duration = completed - started
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        time_taken = f"{minutes}m {seconds}s"
    else:
        time_taken = "In progress"

    # Calculate percentage
    percentage = (session.score / session.total_questions * 100) if session.total_questions > 0 else 0

    # Get words reviewed
    words_reviewed = [q.word for q in session.questions]

    return QuizResultResponse(
        session_id=session.session_id,
        score=session.score,
        total_questions=session.total_questions,
        percentage=percentage,
        time_taken=time_taken,
        words_reviewed=words_reviewed
    )


@router.get("/quiz/stats", name="get_learning_stats")
async def get_learning_stats(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get learning statistics and spaced repetition metrics.

    Returns comprehensive stats for user's vocabulary learning progress
    using SM-2 spaced repetition data.

    **Authentication Required**: Yes

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        dict with learning statistics:
            - total_words: Total vocabulary size
            - new_words: Never reviewed
            - learning: Currently learning (1-4 reviews)
            - mature: Mastered (≥5 reviews, EF≥2.5)
            - due_today: Due for review today
            - due_this_week: Due in next 7 days
            - overdue: Past due date
            - avg_easiness: Average easiness factor
            - success_rate: Overall success rate %

    Example:
        ```bash
        curl http://localhost:8000/api/quiz/stats \
          -H "Authorization: Bearer $TOKEN"
        ```

        Response:
        ```json
        {
          "total_words": 450,
          "new_words": 50,
          "learning": 150,
          "mature": 250,
          "due_today": 25,
          "due_this_week": 75,
          "overdue": 10,
          "avg_easiness": 2.6,
          "success_rate": 85.5
        }
        ```
    """
    # This would query the database for user's vocabulary
    # Placeholder implementation
    return {
        "total_words": 0,
        "new_words": 0,
        "learning": 0,
        "mature": 0,
        "due_today": 0,
        "due_this_week": 0,
        "overdue": 0,
        "avg_easiness": 2.5,
        "success_rate": 0.0
    }


async def _update_spaced_repetition(
    user_id: int,
    word: str,
    quality: ReviewQuality,
    db: AsyncSession
) -> None:
    """
    Update spaced repetition schedule for a word.

    Args:
        user_id: User ID
        word: Vocabulary word
        quality: Review quality
        db: Database session
    """
    # This would update the database with new SR schedule
    # Placeholder implementation
    logger.debug(f"Updating SR for word '{word}', user {user_id}, quality {quality.value}")
