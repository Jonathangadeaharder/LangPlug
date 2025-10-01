"""
Comprehensive Game Routes API Tests

Tests game session management, scoring logic, and user interactions.
Focuses on business outcomes and proper error handling.
"""

from uuid import uuid4

import pytest

from tests.helpers.data_builders import UserBuilder


class TestGameSessionManagement:
    """Test game session lifecycle management"""

    @pytest.fixture
    async def auth_user(self, async_client):
        """Create authenticated user for game tests"""
        user = UserBuilder().build()

        # Register and login user
        register_data = {"username": user.username, "email": user.email, "password": user.password}

        register_response = await async_client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201

        login_data = {"username": user.email, "password": user.password}
        login_response = await async_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"user": user, "token": token}

    @pytest.mark.asyncio
    async def test_WhenStartVocabularyGame_ThenReturnsActiveSession(self, async_client, auth_user):
        """Test starting a vocabulary game session returns active session"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        game_request = {"game_type": "vocabulary", "difficulty": "intermediate", "total_questions": 10}

        response = await async_client.post("/api/game/start", json=game_request, headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify session structure
        assert "session_id" in data
        assert data["game_type"] == "vocabulary"
        assert data["difficulty"] == "intermediate"
        assert data["status"] == "active"
        assert data["total_questions"] == 10
        assert data["current_question"] == 0
        assert data["score"] == 0
        assert data["questions_answered"] == 0
        assert data["correct_answers"] == 0

        # Verify timestamps
        assert "started_at" in data
        assert data["completed_at"] is None

    @pytest.mark.asyncio
    async def test_WhenStartGameWithVideo_ThenIncludesVideoId(self, async_client, auth_user):
        """Test starting game with video context includes video ID"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        video_id = str(uuid4())
        game_request = {"game_type": "listening", "difficulty": "beginner", "video_id": video_id, "total_questions": 5}

        response = await async_client.post("/api/game/start", json=game_request, headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["video_id"] == video_id
        assert data["game_type"] == "listening"

    @pytest.mark.asyncio
    async def test_WhenStartGameWithInvalidType_ThenReturns422(self, async_client, auth_user):
        """Test starting game with invalid game type returns validation error"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        game_request = {"game_type": "invalid_type", "difficulty": "intermediate"}

        response = await async_client.post("/api/game/start", json=game_request, headers=headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_WhenStartGameWithoutAuth_ThenReturns401(self, async_client):
        """Test starting game without authentication returns unauthorized"""
        game_request = {"game_type": "vocabulary", "difficulty": "intermediate"}

        response = await async_client.post("/api/game/start", json=game_request)

        assert response.status_code == 401


class TestGameSessionRetrieval:
    """Test retrieving game session information"""

    @pytest.fixture
    async def auth_user(self, async_client):
        """Create authenticated user for game tests"""
        user = UserBuilder().build()

        # Register and login user
        register_data = {"username": user.username, "email": user.email, "password": user.password}

        register_response = await async_client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201

        login_data = {"username": user.email, "password": user.password}
        login_response = await async_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"user": user, "token": token}

    @pytest.fixture
    async def game_session(self, async_client, auth_user):
        """Create a game session for testing"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        game_request = {"game_type": "vocabulary", "difficulty": "intermediate", "total_questions": 10}

        response = await async_client.post("/api/game/start", json=game_request, headers=headers)
        assert response.status_code == 200
        return response.json()

    @pytest.mark.asyncio
    async def test_WhenGetValidSession_ThenReturnsSessionData(self, async_client, auth_user, game_session):
        """Test retrieving valid game session returns complete data"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        session_id = game_session["session_id"]

        response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == session_id
        assert data["game_type"] == "vocabulary"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_WhenGetNonexistentSession_ThenReturns404(self, async_client, auth_user):
        """Test retrieving nonexistent session returns not found"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        fake_session_id = str(uuid4())

        response = await async_client.get(f"/api/game/session/{fake_session_id}", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_WhenGetSessionWithoutAuth_ThenReturns401(self, async_client, game_session):
        """Test retrieving session without auth returns unauthorized"""
        session_id = game_session["session_id"]

        response = await async_client.get(f"/api/game/session/{session_id}")

        assert response.status_code == 401


class TestGameAnswerSubmission:
    """Test game answer submission and scoring logic"""

    @pytest.fixture
    async def auth_user(self, async_client):
        """Create authenticated user for game tests"""
        user = UserBuilder().build()

        # Register and login user
        register_data = {"username": user.username, "email": user.email, "password": user.password}

        register_response = await async_client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201

        login_data = {"username": user.email, "password": user.password}
        login_response = await async_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"user": user, "token": token}

    @pytest.fixture
    async def active_session(self, async_client, auth_user):
        """Create active game session for answer testing"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        game_request = {"game_type": "vocabulary", "difficulty": "intermediate", "total_questions": 3}

        response = await async_client.post("/api/game/start", json=game_request, headers=headers)
        assert response.status_code == 200
        return response.json()

    @pytest.mark.asyncio
    async def test_WhenSubmitCorrectAnswer_ThenUpdatesScoredAndProgress(self, async_client, auth_user, active_session):
        """Test submitting correct answer updates score and progress"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        # Get the first question from the session data to use the actual correct answer
        session_questions = active_session["session_data"]["questions"]
        first_question = session_questions[0]

        answer_request = {
            "session_id": active_session["session_id"],
            "question_id": first_question["question_id"],
            "question_type": first_question["question_type"],
            "user_answer": first_question["correct_answer"],
            "points": first_question["points"],
        }

        response = await async_client.post("/api/game/answer", json=answer_request, headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify scoring update
        assert data["is_correct"] is True
        assert "points_earned" in data

        # Verify session progress (get updated session)
        session_response = await async_client.get(f"/api/game/session/{active_session['session_id']}", headers=headers)
        session_data = session_response.json()

        assert session_data["questions_answered"] == 1
        assert session_data["correct_answers"] == 1
        assert session_data["current_question"] == 1
        assert session_data["score"] > 0

    @pytest.mark.asyncio
    async def test_WhenSubmitIncorrectAnswer_ThenUpdatesProgressButNotScore(
        self, async_client, auth_user, active_session
    ):
        """Test submitting incorrect answer updates progress but not score"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        # Get the first question from the session data
        session_questions = active_session["session_data"]["questions"]
        first_question = session_questions[0]

        answer_request = {
            "session_id": active_session["session_id"],
            "question_id": first_question["question_id"],
            "question_type": first_question["question_type"],
            "user_answer": "wrong_answer",
            "points": first_question["points"],
        }

        response = await async_client.post("/api/game/answer", json=answer_request, headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["is_correct"] is False
        assert data["points_earned"] == 0

        # Verify session progress
        session_response = await async_client.get(f"/api/game/session/{active_session['session_id']}", headers=headers)
        session_data = session_response.json()

        assert session_data["questions_answered"] == 1
        assert session_data["correct_answers"] == 0
        assert session_data["score"] == 0

    @pytest.mark.asyncio
    async def test_WhenSubmitAnswerForInvalidSession_ThenReturns404(self, async_client, auth_user):
        """Test submitting answer for invalid session returns not found"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        answer_request = {
            "session_id": str(uuid4()),
            "question_id": "q1",
            "user_answer": "any_answer",
            "correct_answer": "correct_answer",
        }

        response = await async_client.post("/api/game/answer", json=answer_request, headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_WhenCompleteAllQuestions_ThenSessionBecomesCompleted(self, async_client, auth_user, active_session):
        """Test completing all questions marks session as completed"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        session_id = active_session["session_id"]

        # Get all questions from the session data
        session_questions = active_session["session_data"]["questions"]

        # Submit answers for all 3 questions
        for _i, question in enumerate(session_questions):
            answer_request = {
                "session_id": session_id,
                "question_id": question["question_id"],
                "question_type": question["question_type"],
                "user_answer": question["correct_answer"],
                "points": question["points"],
            }

            response = await async_client.post("/api/game/answer", json=answer_request, headers=headers)
            assert response.status_code == 200

        # Check final session state
        session_response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)
        session_data = session_response.json()

        assert session_data["questions_answered"] == 3
        assert session_data["status"] == "completed"
        assert session_data["completed_at"] is not None
        assert session_data["score"] == 30  # 3 questions * 10 points each


class TestUserGameSessions:
    """Test listing user's game sessions"""

    @pytest.fixture
    async def auth_user(self, async_client):
        """Create authenticated user for game tests"""
        user = UserBuilder().build()

        # Register and login user
        register_data = {"username": user.username, "email": user.email, "password": user.password}

        register_response = await async_client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201

        login_data = {"username": user.email, "password": user.password}
        login_response = await async_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"user": user, "token": token}

    @pytest.fixture
    async def multiple_sessions(self, async_client, auth_user):
        """Create multiple game sessions for testing"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        sessions = []

        # Create 3 different game sessions
        game_types = ["vocabulary", "listening", "comprehension"]

        for game_type in game_types:
            game_request = {"game_type": game_type, "difficulty": "intermediate", "total_questions": 5}

            response = await async_client.post("/api/game/start", json=game_request, headers=headers)
            assert response.status_code == 200
            sessions.append(response.json())

        return sessions

    @pytest.mark.asyncio
    async def test_WhenGetUserSessions_ThenReturnsAllUserSessions(self, async_client, auth_user, multiple_sessions):
        """Test retrieving user sessions returns all sessions for user"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        response = await async_client.get("/api/game/sessions", headers=headers)

        assert response.status_code == 200
        sessions = response.json()

        assert len(sessions) == 3

        # Verify all sessions belong to user and have correct structure
        game_types = [s["game_type"] for s in sessions]
        assert "vocabulary" in game_types
        assert "listening" in game_types
        assert "comprehension" in game_types

        for session in sessions:
            assert "session_id" in session
            assert "started_at" in session
            assert session["status"] == "active"

    @pytest.mark.asyncio
    async def test_WhenGetSessionsWithoutAuth_ThenReturns401(self, async_client):
        """Test getting sessions without authentication returns unauthorized"""
        response = await async_client.get("/api/game/sessions")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_WhenUserHasNoSessions_ThenReturnsEmptyList(self, async_client, auth_user):
        """Test user with no sessions gets empty list"""
        headers = {"Authorization": f"Bearer {auth_user['token']}"}

        response = await async_client.get("/api/game/sessions", headers=headers)

        assert response.status_code == 200
        assert response.json() == []
