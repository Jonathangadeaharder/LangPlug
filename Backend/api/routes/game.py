"""Game session management API routes"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.config import settings
from core.dependencies import current_active_user
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
    start_time: datetime
    end_time: datetime | None = None
    status: str = "active"  # "active", "completed", "paused", "abandoned"
    score: int = 0
    max_score: int = 100
    questions_answered: int = 0
    correct_answers: int = 0
    current_question: int = 0
    total_questions: int = 10
    session_data: dict[str, Any] = {}


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


class StartGameRequest(BaseModel):
    """Request model for starting a game session"""
    game_type: str
    difficulty: str = "intermediate"
    video_id: str | None = None
    total_questions: int = 10


class AnswerRequest(BaseModel):
    """Request model for submitting an answer"""
    session_id: str
    question_id: str
    answer: str


@router.post("/start", response_model=GameSession, name="game_start_session")
async def start_game_session(
    game_request: StartGameRequest,
    current_user: User = Depends(current_active_user)
):
    """Start a new game session"""
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create new game session
        game_session = GameSession(
            session_id=session_id,
            user_id=str(current_user.id),
            game_type=game_request.game_type,
            difficulty=game_request.difficulty,
            video_id=game_request.video_id,
            start_time=datetime.now(),
            total_questions=game_request.total_questions,
            max_score=game_request.total_questions * 10  # 10 points per question
        )

        # Generate questions based on game type and difficulty
        questions = await generate_game_questions(
            game_request.game_type,
            game_request.difficulty,
            game_request.video_id,
            game_request.total_questions
        )

        # Store questions in session data
        game_session.session_data = {
            "questions": [q.dict() for q in questions],
            "created_at": datetime.now().isoformat()
        }

        # Ensure user data directory exists
        user_data_path = settings.get_data_path() / str(current_user.id) / "game_sessions"
        user_data_path.mkdir(parents=True, exist_ok=True)

        # Save session to file
        session_path = user_data_path / f"{session_id}.json"
        session_dict = game_session.dict()
        session_dict['start_time'] = session_dict['start_time'].isoformat()

        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Started game session {session_id} for user {current_user.id}")
        return game_session

    except Exception as e:
        logger.error(f"Error starting game session: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting game session: {e!s}")


@router.get("/session/{session_id}", response_model=GameSession, name="game_get_session")
async def get_game_session(
    session_id: str,
    current_user: User = Depends(current_active_user)
):
    """Get a specific game session"""
    try:
        session_path = settings.get_data_path() / str(current_user.id) / "game_sessions" / f"{session_id}.json"

        if not session_path.exists():
            raise HTTPException(status_code=404, detail="Game session not found")

        with open(session_path, encoding='utf-8') as f:
            session_data = json.load(f)

        # Convert datetime strings back to datetime objects
        session_data['start_time'] = datetime.fromisoformat(session_data['start_time'])
        if session_data.get('end_time'):
            session_data['end_time'] = datetime.fromisoformat(session_data['end_time'])

        game_session = GameSession(**session_data)

        logger.info(f"Retrieved game session {session_id} for user {current_user.id}")
        return game_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game session: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game session: {e!s}")


@router.post("/answer", name="game_submit_answer")
async def submit_answer(
    answer_request: AnswerRequest,
    current_user: User = Depends(current_active_user)
):
    """Submit an answer for a game question"""
    try:
        # Get current session
        game_session = await get_game_session(answer_request.session_id, current_user)

        if game_session.status != "active":
            raise HTTPException(status_code=400, detail="Game session is not active")

        # Find the question
        questions = game_session.session_data.get("questions", [])
        question = None
        for q in questions:
            if q["question_id"] == answer_request.question_id:
                question = q
                break

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Check if already answered
        if question.get("user_answer") is not None:
            raise HTTPException(status_code=400, detail="Question already answered")

        # Evaluate answer
        is_correct = answer_request.answer.strip().lower() == question["correct_answer"].strip().lower()
        points = question["points"] if is_correct else 0

        # Update question
        question["user_answer"] = answer_request.answer
        question["is_correct"] = is_correct
        question["timestamp"] = datetime.now().isoformat()

        # Update session stats
        game_session.questions_answered += 1
        if is_correct:
            game_session.correct_answers += 1
            game_session.score += points

        game_session.current_question += 1

        # Check if game is completed
        if game_session.questions_answered >= game_session.total_questions:
            game_session.status = "completed"
            game_session.end_time = datetime.now()

        # Save updated session
        session_path = settings.get_data_path() / str(current_user.id) / "game_sessions" / f"{answer_request.session_id}.json"
        session_dict = game_session.dict()
        session_dict['start_time'] = session_dict['start_time'].isoformat()
        if session_dict.get('end_time'):
            session_dict['end_time'] = session_dict['end_time'].isoformat()

        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)

        result = {
            "is_correct": is_correct,
            "points_earned": points,
            "current_score": game_session.score,
            "questions_remaining": game_session.total_questions - game_session.questions_answered,
            "session_completed": game_session.status == "completed"
        }

        logger.info(f"Answer submitted for session {answer_request.session_id}, correct: {is_correct}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {e!s}")


@router.get("/sessions", response_model=list[GameSession], name="game_get_user_sessions")
async def get_user_game_sessions(
    limit: int = 10,
    current_user: User = Depends(current_active_user)
):
    """Get user's game sessions"""
    try:
        sessions_path = settings.get_data_path() / str(current_user.id) / "game_sessions"

        if not sessions_path.exists():
            return []

        sessions = []
        session_files = list(sessions_path.glob("*.json"))

        # Sort by creation time (most recent first)
        session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for session_file in session_files[:limit]:
            try:
                with open(session_file, encoding='utf-8') as f:
                    session_data = json.load(f)

                # Convert datetime strings
                session_data['start_time'] = datetime.fromisoformat(session_data['start_time'])
                if session_data.get('end_time'):
                    session_data['end_time'] = datetime.fromisoformat(session_data['end_time'])

                sessions.append(GameSession(**session_data))

            except Exception as e:
                logger.warning(f"Error loading session file {session_file}: {e!s}")
                continue

        logger.info(f"Retrieved {len(sessions)} game sessions for user {current_user.id}")
        return sessions

    except Exception as e:
        logger.error(f"Error getting user game sessions: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game sessions: {e!s}")


async def generate_game_questions(
    game_type: str,
    difficulty: str,
    video_id: str | None,
    total_questions: int
) -> list[GameQuestion]:
    """Generate questions for a game session"""
    questions = []

    # Sample questions based on game type
    if game_type == "vocabulary":
        sample_words = [
            {"word": "hello", "translation": "hola", "difficulty": "beginner"},
            {"word": "goodbye", "translation": "adiós", "difficulty": "beginner"},
            {"word": "beautiful", "translation": "hermoso", "difficulty": "intermediate"},
            {"word": "complicated", "translation": "complicado", "difficulty": "advanced"},
            {"word": "understand", "translation": "entender", "difficulty": "intermediate"},
        ]

        # Filter by difficulty
        filtered_words = [w for w in sample_words if w["difficulty"] == difficulty]
        if not filtered_words:
            filtered_words = sample_words  # Fallback to all words

        for i in range(min(total_questions, len(filtered_words))):
            word_data = filtered_words[i % len(filtered_words)]
            question = GameQuestion(
                question_id=str(uuid.uuid4()),
                question_type="translation",
                question_text=f"What is the translation of '{word_data['word']}'?",
                correct_answer=word_data["translation"],
                points=10
            )
            questions.append(question)

    elif game_type == "listening":
        # Generate listening comprehension questions
        for i in range(total_questions):
            question = GameQuestion(
                question_id=str(uuid.uuid4()),
                question_type="multiple_choice",
                question_text=f"What did the speaker say in segment {i+1}?",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                points=10
            )
            questions.append(question)

    else:  # comprehension
        # Generate comprehension questions
        for i in range(total_questions):
            question = GameQuestion(
                question_id=str(uuid.uuid4()),
                question_type="multiple_choice",
                question_text=f"What was the main idea of segment {i+1}?",
                options=["Idea A", "Idea B", "Idea C", "Idea D"],
                correct_answer="Idea A",
                points=10
            )
            questions.append(question)

    return questions
