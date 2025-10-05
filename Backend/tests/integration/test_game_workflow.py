"""
Game Workflow Integration Tests

Tests complete game session workflows including user authentication,
session management, question flow, and scoring across multiple endpoints.
"""

from uuid import uuid4

import pytest

from tests.helpers import AuthTestHelperAsync
from tests.helpers.data_builders import UserBuilder


class TestCompleteGameWorkflow:
    """Test end-to-end game session workflows"""

    @pytest.fixture
    async def authenticated_user(self, async_client):
        """Create and authenticate a user for game testing"""
        user = UserBuilder().build()

        # Register user
        register_data = {"username": user.username, "email": user.email, "password": user.password}
        register_response = await async_client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201

        # Login user
        login_data = {"username": user.email, "password": user.password}
        login_response = await async_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

    @pytest.mark.asyncio
    async def test_WhenCompleteVocabularyGameWorkflow_ThenSucceedsWithCorrectScoring(
        self, async_client, authenticated_user
    ):
        """Test complete vocabulary game workflow from start to finish"""
        headers = authenticated_user["headers"]

        # Step 1: Start vocabulary game session
        start_request = {"game_type": "vocabulary", "difficulty": "intermediate", "total_questions": 3}

        start_response = await async_client.post("/api/game/start", json=start_request, headers=headers)
        assert start_response.status_code == 200

        session_data = start_response.json()
        session_id = session_data["session_id"]

        # Verify initial session state
        assert session_data["status"] == "active"
        assert session_data["score"] == 0
        assert session_data["questions_answered"] == 0
        assert session_data["current_question"] == 0

        # Step 2: Answer first question (correct)
        # Note: Game generates questions with rotating words, q1 uses intermediate level word "hermoso"
        answer1_request = {
            "session_id": session_id,
            "question_id": "q1",  # Fixed: Use correct question ID format
            "question_type": "translation",  # Fixed: Use correct question type
            "user_answer": "hermoso",  # Fixed: Use correct translation for "beautiful"
            "correct_answer": "hermoso",
            "points": 10,
        }

        answer1_response = await async_client.post("/api/game/answer", json=answer1_request, headers=headers)
        assert answer1_response.status_code == 200

        answer1_data = answer1_response.json()
        assert answer1_data["is_correct"] is True
        assert answer1_data["points_earned"] == 10

        # Step 3: Get session after first answer
        session1_response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)
        assert session1_response.status_code == 200

        session1_data = session1_response.json()
        assert session1_data["questions_answered"] == 1
        assert session1_data["correct_answers"] == 1
        assert session1_data["current_question"] == 1
        assert session1_data["score"] == 10

        # Step 4: Answer second question (incorrect)
        # Note: q2 uses the second intermediate word "entender"
        answer2_request = {
            "session_id": session_id,
            "question_id": "q2",  # Fixed: Use correct question ID format
            "question_type": "translation",  # Fixed: Use correct question type
            "user_answer": "wrong answer",  # Intentionally wrong for test
            "correct_answer": "entender",  # Fixed: Use correct translation for "understand"
            "points": 10,
        }

        answer2_response = await async_client.post("/api/game/answer", json=answer2_request, headers=headers)
        assert answer2_response.status_code == 200

        answer2_data = answer2_response.json()
        assert answer2_data["is_correct"] is False
        assert answer2_data["points_earned"] == 0

        # Step 5: Answer third question (correct)
        # Note: q3 cycles back to index 0 (hermoso) since there are only 2 intermediate words
        answer3_request = {
            "session_id": session_id,
            "question_id": "q3",  # Fixed: Use correct question ID format
            "question_type": "translation",
            "user_answer": "hermoso",  # Fixed: Correct Spanish translation for "beautiful"
            "correct_answer": "hermoso",
            "points": 10,  # Fixed: Use correct default points value
        }

        answer3_response = await async_client.post("/api/game/answer", json=answer3_request, headers=headers)
        assert answer3_response.status_code == 200

        answer3_data = answer3_response.json()
        assert answer3_data["is_correct"] is True
        assert answer3_data["points_earned"] == 10  # Fixed: Use correct default points value

        # Step 6: Get final session state
        final_session_response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)
        assert final_session_response.status_code == 200

        final_session_data = final_session_response.json()

        # Verify final session statistics
        assert final_session_data["questions_answered"] == 3
        assert final_session_data["correct_answers"] == 2
        assert final_session_data["score"] == 20  # Fixed: 10 + 0 + 10 (correct scoring)
        assert final_session_data["status"] == "completed"
        assert final_session_data["completed_at"] is not None  # Fixed: Use correct field name

        # Step 7: Verify session appears in user's session list
        sessions_response = await async_client.get("/api/game/sessions", headers=headers)
        assert sessions_response.status_code == 200

        user_sessions = sessions_response.json()
        assert len(user_sessions) == 1
        assert user_sessions[0]["session_id"] == session_id
        assert user_sessions[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_WhenMultipleGameSessions_ThenEachSessionIsIndependent(self, async_client, authenticated_user):
        """Test multiple concurrent game sessions remain independent"""
        headers = authenticated_user["headers"]

        # Create two different game sessions
        vocab_session_request = {"game_type": "vocabulary", "difficulty": "beginner", "total_questions": 2}

        listening_session_request = {
            "game_type": "listening",
            "difficulty": "advanced",
            "video_id": str(uuid4()),
            "total_questions": 2,
        }

        # Start both sessions
        vocab_response = await async_client.post("/api/game/start", json=vocab_session_request, headers=headers)
        listening_response = await async_client.post("/api/game/start", json=listening_session_request, headers=headers)

        assert vocab_response.status_code == 200
        assert listening_response.status_code == 200

        vocab_session = vocab_response.json()
        listening_session = listening_response.json()

        # Verify sessions are different
        assert vocab_session["session_id"] != listening_session["session_id"]
        assert vocab_session["game_type"] == "vocabulary"
        assert listening_session["game_type"] == "listening"

        # Answer question in vocabulary session
        # Note: vocab session uses beginner difficulty -> first word should be "hello" -> "hola"
        vocab_answer = {
            "session_id": vocab_session["session_id"],
            "question_id": "q1",  # Fixed: Use correct question ID format
            "question_type": "translation",  # Fixed: Use correct question type
            "user_answer": "hola",  # Fixed: Use actual beginner vocabulary translation for "hello"
            "correct_answer": "hola",
            "points": 10,  # Fixed: Use default points value
        }

        vocab_answer_response = await async_client.post("/api/game/answer", json=vocab_answer, headers=headers)
        assert vocab_answer_response.status_code == 200

        # Answer question in listening session
        # Note: listening session generates multiple_choice questions with "Option A" as correct answer
        listening_answer = {
            "session_id": listening_session["session_id"],
            "question_id": "q1",  # Fixed: Use correct question ID format
            "question_type": "multiple_choice",  # Fixed: Use correct question type for listening
            "user_answer": "wrong answer",  # Intentionally wrong
            "correct_answer": "Option A",  # Fixed: Use actual listening game correct answer
            "points": 10,  # Fixed: Use default points value
        }

        listening_answer_response = await async_client.post("/api/game/answer", json=listening_answer, headers=headers)
        assert listening_answer_response.status_code == 200

        # Verify independent scoring
        vocab_final = await async_client.get(f"/api/game/session/{vocab_session['session_id']}", headers=headers)
        listening_final = await async_client.get(
            f"/api/game/session/{listening_session['session_id']}", headers=headers
        )

        vocab_data = vocab_final.json()
        listening_data = listening_final.json()

        # Vocabulary session should have score of 10 (correct answer)
        assert vocab_data["score"] == 10
        assert vocab_data["correct_answers"] == 1

        # Listening session should have score of 0
        assert listening_data["score"] == 0
        assert listening_data["correct_answers"] == 0

        # Both should be active (not completed yet)
        assert vocab_data["status"] == "active"
        assert listening_data["status"] == "active"

        # User should have 2 sessions
        sessions_response = await async_client.get("/api/game/sessions", headers=headers)
        sessions = sessions_response.json()
        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_WhenVideoGameWorkflow_ThenIncludesVideoContext(self, async_client, authenticated_user):
        """Test video-based game workflow includes video context"""
        headers = authenticated_user["headers"]
        video_id = str(uuid4())

        # Start video-based listening game
        start_request = {
            "game_type": "listening",
            "difficulty": "intermediate",
            "video_id": video_id,
            "total_questions": 2,
        }

        start_response = await async_client.post("/api/game/start", json=start_request, headers=headers)
        assert start_response.status_code == 200

        session_data = start_response.json()
        session_id = session_data["session_id"]

        # Verify video context is preserved
        assert session_data["video_id"] == video_id
        assert session_data["game_type"] == "listening"

        # Answer listening comprehension question
        answer_request = {
            "session_id": session_id,
            "question_id": "q1",  # Fixed: Use correct question ID format
            "question_type": "multiple_choice",  # Fixed: Use correct question type for listening
            "user_answer": "Option A",  # Fixed: Use actual listening game correct answer
            "correct_answer": "Option A",
            "points": 10,  # Fixed: Use default points value
        }

        answer_response = await async_client.post("/api/game/answer", json=answer_request, headers=headers)
        assert answer_response.status_code == 200

        # Verify session retains video context after answer
        session_response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)
        session_current = session_response.json()

        assert session_current["video_id"] == video_id
        assert session_current["score"] == 10  # Fixed: Use correct default points
        assert session_current["status"] == "active"  # Not complete yet (2 questions total)

    @pytest.mark.asyncio
    async def test_WhenGameSessionErrorRecovery_ThenHandlesGracefully(self, async_client, authenticated_user):
        """Test error scenarios and recovery in game workflow"""
        headers = authenticated_user["headers"]

        # Start valid session
        start_request = {"game_type": "vocabulary", "difficulty": "intermediate", "total_questions": 2}

        start_response = await async_client.post("/api/game/start", json=start_request, headers=headers)
        assert start_response.status_code == 200

        session_data = start_response.json()
        session_id = session_data["session_id"]

        # Try to answer with invalid session ID
        invalid_answer = {
            "session_id": str(uuid4()),  # Wrong session ID
            "question_id": "q1",
            "question_type": "translation",  # Fixed: Add required question type
            "user_answer": "hermoso",  # Fixed: Use actual vocabulary translation
            "correct_answer": "hermoso",
        }

        invalid_response = await async_client.post("/api/game/answer", json=invalid_answer, headers=headers)
        assert invalid_response.status_code == 404

        # Verify original session is unaffected
        session_response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)
        assert session_response.status_code == 200

        session_current = session_response.json()
        assert session_current["questions_answered"] == 0  # No changes from failed attempt
        assert session_current["score"] == 0

        # Successfully answer with correct session ID
        valid_answer = {
            "session_id": session_id,
            "question_id": "q1",
            "question_type": "translation",  # Fixed: Add required question type
            "user_answer": "hermoso",  # Fixed: Use actual vocabulary translation
            "correct_answer": "hermoso",
            "points": 10,
        }

        valid_response = await async_client.post("/api/game/answer", json=valid_answer, headers=headers)
        assert valid_response.status_code == 200

        # Verify session updated correctly
        final_session_response = await async_client.get(f"/api/game/session/{session_id}", headers=headers)
        final_session = final_session_response.json()

        assert final_session["questions_answered"] == 1
        assert final_session["score"] == 10

    @pytest.mark.asyncio
    async def test_WhenMultiUserGameSessions_ThenSessionsIsolated(self, async_client):
        """Test game sessions are properly isolated between different users"""
        # Create and authenticate two different users using consistent patterns
        user1_flow = await AuthTestHelperAsync.register_and_login_async(async_client)
        user2_flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        user_tokens = {"user1": {"headers": user1_flow["headers"]}, "user2": {"headers": user2_flow["headers"]}}

        # Each user starts a game session
        start_request = {"game_type": "vocabulary", "difficulty": "intermediate", "total_questions": 1}

        user1_session_response = await async_client.post(
            "/api/game/start", json=start_request, headers=user_tokens["user1"]["headers"]
        )
        user2_session_response = await async_client.post(
            "/api/game/start", json=start_request, headers=user_tokens["user2"]["headers"]
        )

        assert user1_session_response.status_code == 200
        assert user2_session_response.status_code == 200

        user1_session = user1_session_response.json()
        user2_session = user2_session_response.json()

        # Verify sessions are different
        assert user1_session["session_id"] != user2_session["session_id"]

        # User 1 cannot access User 2's session
        user1_accessing_user2 = await async_client.get(
            f"/api/game/session/{user2_session['session_id']}", headers=user_tokens["user1"]["headers"]
        )
        assert user1_accessing_user2.status_code == 404  # Should not find other user's session

        # User 2 cannot access User 1's session
        user2_accessing_user1 = await async_client.get(
            f"/api/game/session/{user1_session['session_id']}", headers=user_tokens["user2"]["headers"]
        )
        assert user2_accessing_user1.status_code == 404

        # Each user can only see their own sessions
        user1_sessions = await async_client.get("/api/game/sessions", headers=user_tokens["user1"]["headers"])
        user2_sessions = await async_client.get("/api/game/sessions", headers=user_tokens["user2"]["headers"])

        user1_sessions_data = user1_sessions.json()
        user2_sessions_data = user2_sessions.json()

        assert len(user1_sessions_data) == 1
        assert len(user2_sessions_data) == 1
        assert user1_sessions_data[0]["session_id"] == user1_session["session_id"]
        assert user2_sessions_data[0]["session_id"] == user2_session["session_id"]
