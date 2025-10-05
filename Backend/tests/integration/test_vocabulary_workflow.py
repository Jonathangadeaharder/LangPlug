"""
Vocabulary Learning Workflow Integration Tests

Tests complete vocabulary learning workflows including user progress tracking,
multilingual support, and statistical consistency across the application.
"""

import pytest

from tests.helpers import AuthTestHelperAsync
from tests.helpers.data_builders import UserBuilder


class TestCompleteVocabularyLearningWorkflow:
    """Test end-to-end vocabulary learning workflows"""

    @pytest.fixture
    async def authenticated_user(self, async_client):
        """Create and authenticate a user for vocabulary testing"""
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
    async def test_WhenCompleteVocabularyProgressionWorkflow_ThenAllStepsSucceed(
        self, async_client, authenticated_user
    ):
        """Test complete vocabulary learning progression workflow"""
        headers = authenticated_user["headers"]

        # Step 1: Get supported languages (may be empty in test environment)
        languages_response = await async_client.get("/api/vocabulary/languages", headers=headers)
        assert languages_response.status_code == 200
        languages = languages_response.json()
        assert "languages" in languages
        # Languages list may be empty if no languages are configured
        assert isinstance(languages["languages"], list)

        # Step 2: Get initial vocabulary statistics
        initial_stats_response = await async_client.get(
            "/api/vocabulary/stats", params={"target_language": "de", "translation_language": "es"}, headers=headers
        )
        assert initial_stats_response.status_code == 200
        initial_stats = initial_stats_response.json()

        assert "levels" in initial_stats
        assert "total_words" in initial_stats
        assert "total_known" in initial_stats
        initial_total_known = initial_stats["total_known"]

        # Step 3: Get vocabulary words from A1 level
        a1_words_response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "de", "translation_language": "es", "limit": 5},
            headers=headers,
        )
        assert a1_words_response.status_code == 200
        a1_words = a1_words_response.json()

        assert "words" in a1_words
        assert "level" in a1_words
        assert a1_words["level"] == "A1"

        if not a1_words["words"]:
            pytest.skip("No A1 vocabulary words available for workflow test")

        # Step 4: Mark some words as known
        words_marked = 0
        for word in a1_words["words"][:3]:  # Mark first 3 words as known
            mark_response = await async_client.post(
                "/api/vocabulary/mark-known", json={"concept_id": word["concept_id"], "known": True}, headers=headers
            )
            assert mark_response.status_code == 200
            mark_data = mark_response.json()
            assert mark_data["success"] is True
            assert mark_data["known"] is True
            words_marked += 1

        # Step 5: Verify statistics updated correctly
        updated_stats_response = await async_client.get(
            "/api/vocabulary/stats", params={"target_language": "de", "translation_language": "es"}, headers=headers
        )
        assert updated_stats_response.status_code == 200
        updated_stats = updated_stats_response.json()

        # Total known should have increased
        assert updated_stats["total_known"] >= initial_total_known + words_marked

        # Step 6: Verify A1 level reflects changes
        updated_a1_response = await async_client.get(
            "/api/vocabulary/library/A1",
            params={"target_language": "de", "translation_language": "es", "limit": 5},
            headers=headers,
        )
        assert updated_a1_response.status_code == 200
        updated_a1_words = updated_a1_response.json()

        # Known count should have increased
        assert updated_a1_words["known_count"] >= a1_words["known_count"] + words_marked

        # Verify marked words show as known
        marked_word_ids = {w["concept_id"] for w in a1_words["words"][:3]}
        for word in updated_a1_words["words"]:
            if word["concept_id"] in marked_word_ids:
                assert word["known"] is True

    @pytest.mark.asyncio
    async def test_WhenMultiLevelVocabularyProgression_ThenProgressTracksAcrossLevels(
        self, async_client, authenticated_user
    ):
        """Test vocabulary progression across multiple CEFR levels"""
        headers = authenticated_user["headers"]

        # Get initial stats
        initial_stats_response = await async_client.get("/api/vocabulary/stats", headers=headers)
        assert initial_stats_response.status_code == 200
        initial_stats = initial_stats_response.json()

        # Work with multiple levels
        levels_to_test = ["A1", "A2", "B1"]
        words_marked_per_level = {}

        for level in levels_to_test:
            # Get words for level
            level_response = await async_client.get(
                f"/api/vocabulary/library/{level}", params={"limit": 2}, headers=headers
            )
            assert level_response.status_code == 200
            level_data = level_response.json()

            words_marked_per_level[level] = 0

            # Mark some words as known
            for word in level_data["words"][:2]:  # Mark first 2 words per level
                mark_response = await async_client.post(
                    "/api/vocabulary/mark-known",
                    json={"concept_id": word["concept_id"], "known": True},
                    headers=headers,
                )
                if mark_response.status_code == 200:
                    words_marked_per_level[level] += 1

        # Verify final statistics
        final_stats_response = await async_client.get("/api/vocabulary/stats", headers=headers)
        assert final_stats_response.status_code == 200
        final_stats = final_stats_response.json()

        # Total known should reflect all marked words
        total_marked = sum(words_marked_per_level.values())
        assert final_stats["total_known"] >= initial_stats["total_known"] + total_marked

        # Each level should show increased known count
        for level in levels_to_test:
            if words_marked_per_level[level] > 0:
                assert (
                    final_stats["levels"][level]["user_known"]
                    >= initial_stats["levels"][level]["user_known"] + words_marked_per_level[level]
                )

    @pytest.mark.asyncio
    async def test_WhenBulkVocabularyOperations_ThenConsistentWithIndividualOperations(
        self, async_client, authenticated_user
    ):
        """Test bulk vocabulary operations maintain consistency"""
        headers = authenticated_user["headers"]

        # Get A1 words to compare bulk vs individual operations
        a1_response = await async_client.get("/api/vocabulary/library/A1", params={"limit": 100}, headers=headers)
        assert a1_response.status_code == 200
        a1_response.json()

        # Perform bulk mark operation
        bulk_response = await async_client.post(
            "/api/vocabulary/library/bulk-mark",
            json={"level": "A1", "target_language": "de", "known": True},
            headers=headers,
        )
        assert bulk_response.status_code == 200
        bulk_data = bulk_response.json()

        assert bulk_data["success"] is True
        assert bulk_data["level"] == "A1"
        assert bulk_data["known"] is True
        assert "word_count" in bulk_data

        # Verify all A1 words are now marked as known
        updated_a1_response = await async_client.get(
            "/api/vocabulary/library/A1", params={"limit": 100}, headers=headers
        )
        assert updated_a1_response.status_code == 200
        updated_a1_data = updated_a1_response.json()

        # All words should now be marked as known
        for word in updated_a1_data["words"]:
            assert word["known"] is True

        # Known count should equal total count
        assert updated_a1_data["known_count"] == updated_a1_data["total_count"]

        # Statistics should reflect bulk change
        stats_response = await async_client.get("/api/vocabulary/stats", headers=headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()

        # A1 level should show all words as known
        assert stats["levels"]["A1"]["user_known"] == stats["levels"]["A1"]["total_words"]

    @pytest.mark.asyncio
    async def test_WhenSwitchingLanguageCombinations_ThenDataRemainsConsistent(self, async_client, authenticated_user):
        """Test switching between different language combinations maintains data consistency"""
        headers = authenticated_user["headers"]

        # Test with German-Spanish combination
        de_es_stats_response = await async_client.get(
            "/api/vocabulary/stats", params={"target_language": "de", "translation_language": "es"}, headers=headers
        )
        assert de_es_stats_response.status_code == 200
        de_es_stats = de_es_stats_response.json()

        # Test with German-English combination
        de_en_stats_response = await async_client.get(
            "/api/vocabulary/stats", params={"target_language": "de", "translation_language": "en"}, headers=headers
        )
        assert de_en_stats_response.status_code == 200
        de_en_stats = de_en_stats_response.json()

        # Core vocabulary counts should be the same (target language is same)
        assert de_es_stats["target_language"] == de_en_stats["target_language"]
        assert de_es_stats["total_words"] == de_en_stats["total_words"]
        assert de_es_stats["total_known"] == de_en_stats["total_known"]

        # Level breakdowns should be identical
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            assert de_es_stats["levels"][level]["total_words"] == de_en_stats["levels"][level]["total_words"]
            assert de_es_stats["levels"][level]["user_known"] == de_en_stats["levels"][level]["user_known"]

        # Translation languages should differ
        assert de_es_stats["translation_language"] == "es"
        assert de_en_stats["translation_language"] == "en"

    @pytest.mark.asyncio
    async def test_WhenVocabularyProgressionWithUnmarkingWords_ThenStatisticsAdjustCorrectly(
        self, async_client, authenticated_user
    ):
        """Test complete workflow including unmarking words"""
        headers = authenticated_user["headers"]

        # Get initial state
        initial_stats = await async_client.get("/api/vocabulary/stats", headers=headers)
        initial_known = initial_stats.json()["total_known"]

        # Get some words to work with
        words_response = await async_client.get("/api/vocabulary/library/A1", params={"limit": 3}, headers=headers)
        assert words_response.status_code == 200
        words_data = words_response.json()

        if not words_data["words"]:
            pytest.skip("No vocabulary words available for unmarking test")

        test_words = words_data["words"][:3]

        # Mark words as known
        for word in test_words:
            mark_response = await async_client.post(
                "/api/vocabulary/mark-known", json={"concept_id": word["concept_id"], "known": True}, headers=headers
            )
            assert mark_response.status_code == 200

        # Verify increase in known count
        mid_stats = await async_client.get("/api/vocabulary/stats", headers=headers)
        mid_known = mid_stats.json()["total_known"]
        assert mid_known >= initial_known + len(test_words)

        # Unmark some words
        words_to_unmark = test_words[:2]  # Unmark first 2
        for word in words_to_unmark:
            unmark_response = await async_client.post(
                "/api/vocabulary/mark-known", json={"concept_id": word["concept_id"], "known": False}, headers=headers
            )
            assert unmark_response.status_code == 200
            unmark_data = unmark_response.json()
            assert unmark_data["success"] is True
            assert unmark_data["known"] is False

        # Verify final statistics
        final_stats = await async_client.get("/api/vocabulary/stats", headers=headers)
        final_known = final_stats.json()["total_known"]

        # Should have only 1 word marked as known now (3 marked, 2 unmarked)
        expected_known = initial_known + 1
        assert final_known == expected_known

        # Verify individual word status
        final_words_response = await async_client.get(
            "/api/vocabulary/library/A1", params={"limit": 10}, headers=headers
        )
        final_words_data = final_words_response.json()

        unmarked_ids = {w["concept_id"] for w in words_to_unmark}
        still_known_ids = {w["concept_id"] for w in test_words[2:]}  # Last word should still be known

        for word in final_words_data["words"]:
            if word["concept_id"] in unmarked_ids:
                assert word["known"] is False
            elif word["concept_id"] in still_known_ids:
                assert word["known"] is True


class TestMultiUserVocabularyIsolation:
    """Test vocabulary progress isolation between different users"""

    @pytest.mark.asyncio
    async def test_WhenMultipleUsersMarkSameWords_ThenProgressIsolatedPerUser(self, async_client):
        """Test vocabulary progress is properly isolated between users"""
        # Create and authenticate two different users using consistent patterns
        user1_flow = await AuthTestHelperAsync.register_and_login_async(async_client)
        user2_flow = await AuthTestHelperAsync.register_and_login_async(async_client)

        user_tokens = {"user1": {"headers": user1_flow["headers"]}, "user2": {"headers": user2_flow["headers"]}}

        # Get same vocabulary words for both users
        words_response = await async_client.get(
            "/api/vocabulary/library/A1", params={"limit": 3}, headers=user_tokens["user1"]["headers"]
        )
        assert words_response.status_code == 200
        words_data = words_response.json()

        if not words_data["words"]:
            pytest.skip("No vocabulary words available for multi-user test")

        test_words = words_data["words"]

        # User 1 marks words as known
        for word in test_words:
            mark_response = await async_client.post(
                "/api/vocabulary/mark-known",
                json={"concept_id": word["concept_id"], "known": True},
                headers=user_tokens["user1"]["headers"],
            )
            assert mark_response.status_code == 200

        # User 2 keeps words as unknown (doesn't mark them)

        # Check User 1's progress
        user1_stats = await async_client.get("/api/vocabulary/stats", headers=user_tokens["user1"]["headers"])
        assert user1_stats.status_code == 200
        user1_known = user1_stats.json()["total_known"]

        # Check User 2's progress
        user2_stats = await async_client.get("/api/vocabulary/stats", headers=user_tokens["user2"]["headers"])
        assert user2_stats.status_code == 200
        user2_known = user2_stats.json()["total_known"]

        # User 1 should have more known words than User 2
        assert user1_known >= user2_known + len(test_words)

        # Verify individual word status for each user
        user1_words = await async_client.get(
            "/api/vocabulary/library/A1", params={"limit": 10}, headers=user_tokens["user1"]["headers"]
        )
        user2_words = await async_client.get(
            "/api/vocabulary/library/A1", params={"limit": 10}, headers=user_tokens["user2"]["headers"]
        )

        marked_word_ids = {w["concept_id"] for w in test_words}

        # Check User 1 sees marked words as known
        for word in user1_words.json()["words"]:
            if word["concept_id"] in marked_word_ids:
                assert word["known"] is True

        # Check User 2 sees same words as unknown
        for word in user2_words.json()["words"]:
            if word["concept_id"] in marked_word_ids:
                assert word["known"] is False
