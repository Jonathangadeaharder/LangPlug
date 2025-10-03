"""
Integration tests for vocabulary service using the new architecture
"""

import pytest
from sqlalchemy.orm import Session

from database.repositories import UserVocabularyProgressRepository, VocabularyRepositorySync
from domains.vocabulary.models import BulkMarkWordsRequest, MarkWordRequest
from domains.vocabulary.services import VocabularyService


@pytest.mark.asyncio
@pytest.mark.integration
class TestVocabularyServiceIntegration:
    """Integration tests for vocabulary service"""

    @pytest.fixture(autouse=True)
    def setup(self, isolated_db_session: Session):
        """Setup for each test"""
        self.db_session = isolated_db_session
        self.vocabulary_repository = VocabularyRepositorySync()
        self.progress_repository = UserVocabularyProgressRepository()
        self.vocabulary_service = VocabularyService(self.vocabulary_repository, self.progress_repository)

    async def test_search_words_integration(self, test_vocabulary_words):
        """Test word search functionality"""
        # Test basic search
        results = await self.vocabulary_service.search_words(self.db_session, "Hund", language="de", limit=10)

        assert len(results) == 1
        assert results[0].word == "der Hund"
        assert results[0].lemma == "Hund"

        # Test partial search
        results = await self.vocabulary_service.search_words(self.db_session, "Ka", language="de", limit=10)

        assert len(results) == 1
        assert results[0].word == "die Katze"

    async def test_get_words_by_level_integration(self, test_vocabulary_words):
        """Test fetching words by difficulty level"""
        # Test A1 level
        a1_words = await self.vocabulary_service.get_words_by_level(self.db_session, "A1", language="de")

        assert len(a1_words) == 2  # Hund and Katze
        assert all(word.difficulty_level == "A1" for word in a1_words)

        # Test A2 level
        a2_words = await self.vocabulary_service.get_words_by_level(self.db_session, "A2", language="de")

        assert len(a2_words) == 1  # laufen
        assert a2_words[0].word == "laufen"

    async def test_mark_word_known_integration(self, test_user, test_vocabulary_words):
        """Test marking word as known/unknown"""
        word = test_vocabulary_words[0]  # der Hund

        # Mark word as known
        request = MarkWordRequest(vocabulary_id=word.id, is_known=True)
        progress = await self.vocabulary_service.mark_word_known(self.db_session, test_user.id, request)

        assert progress.is_known is True
        assert progress.vocabulary_id == word.id
        assert progress.user_id == test_user.id
        assert progress.review_count == 1

        # Mark word as unknown
        request = MarkWordRequest(vocabulary_id=word.id, is_known=False)
        progress = await self.vocabulary_service.mark_word_known(self.db_session, test_user.id, request)

        assert progress.is_known is False
        assert progress.review_count == 2

    async def test_bulk_mark_words_integration(self, test_user, test_vocabulary_words):
        """Test bulk marking words"""
        word_ids = [word.id for word in test_vocabulary_words[:2]]

        # Bulk mark as known
        request = BulkMarkWordsRequest(vocabulary_ids=word_ids, is_known=True)
        progress_list = await self.vocabulary_service.bulk_mark_words(self.db_session, test_user.id, request)

        assert len(progress_list) == 2
        assert all(progress.is_known is True for progress in progress_list)
        assert all(progress.user_id == test_user.id for progress in progress_list)

    async def test_vocabulary_stats_integration(self, test_user, test_user_progress):
        """Test vocabulary statistics calculation"""
        stats = await self.vocabulary_service.get_vocabulary_stats(self.db_session, test_user.id, language="de")

        assert stats.total_reviewed == 2
        assert stats.known_words == 1
        assert stats.unknown_words == 1
        assert stats.percentage_known == 50.0

    async def test_get_user_progress_integration(self, test_user, test_user_progress):
        """Test fetching user progress"""
        progress_list = await self.vocabulary_service.get_user_progress(self.db_session, test_user.id, language="de")

        assert len(progress_list) == 2
        assert progress_list[0].user_id == test_user.id
        assert progress_list[1].user_id == test_user.id

        # Check that one is known and one is unknown
        known_count = sum(1 for p in progress_list if p.is_known)
        unknown_count = sum(1 for p in progress_list if not p.is_known)

        assert known_count == 1
        assert unknown_count == 1

    async def test_get_random_words_integration(self, test_vocabulary_words):
        """Test getting random words"""
        # Test with specific levels
        random_words = await self.vocabulary_service.get_random_words(
            self.db_session, language="de", difficulty_levels=["A1", "A2"], limit=5
        )

        assert len(random_words) <= 5
        assert all(word.difficulty_level in ["A1", "A2"] for word in random_words)

        # Test without level restriction
        all_random_words = await self.vocabulary_service.get_random_words(self.db_session, language="de", limit=10)

        assert len(all_random_words) <= 10

    async def test_get_blocking_words_integration(self, test_user, test_vocabulary_words):
        """Test getting blocking words from text"""
        # Mark first word as known
        word1 = test_vocabulary_words[0]
        request = MarkWordRequest(vocabulary_id=word1.id, is_known=True)
        await self.vocabulary_service.mark_word_known(self.db_session, test_user.id, request)

        # Test text with mixed known/unknown words
        test_text = "der Hund laufen"
        blocking_words = await self.vocabulary_service.get_blocking_words(
            self.db_session, test_user.id, test_text, language="de"
        )

        # Should include "laufen" but not "der" or "Hund" (Hund is marked as known)
        assert "laufen" in blocking_words
        assert "Hund" not in blocking_words


@pytest.mark.integration
class TestVocabularyAPIIntegration:
    """Integration tests for vocabulary API endpoints"""

    def test_vocabulary_search_endpoint(self, client, authenticated_user, test_vocabulary_words):
        """Test vocabulary search API endpoint"""
        headers = authenticated_user["headers"]

        response = client.get(
            "/vocabulary/search", params={"query": "Hund", "language": "de", "limit": 10}, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["word"] == "der Hund"

    def test_vocabulary_level_endpoint(self, client, authenticated_user, test_vocabulary_words):
        """Test vocabulary by level API endpoint"""
        headers = authenticated_user["headers"]

        response = client.get("/vocabulary/level/A1", params={"language": "de"}, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Hund and Katze
        assert all(word["difficulty_level"] == "A1" for word in data)

    def test_mark_word_endpoint(self, client, authenticated_user, test_vocabulary_words):
        """Test mark word API endpoint"""
        headers = authenticated_user["headers"]
        word = test_vocabulary_words[0]

        response = client.post("/vocabulary/mark", json={"vocabulary_id": word.id, "is_known": True}, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_known"] is True
        assert data["vocabulary_id"] == word.id

    def test_vocabulary_stats_endpoint(self, client, authenticated_user, test_user_progress):
        """Test vocabulary stats API endpoint"""
        headers = authenticated_user["headers"]

        response = client.get("/vocabulary/stats", params={"language": "de"}, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_reviewed" in data
        assert "known_words" in data
        assert "unknown_words" in data
        assert "percentage_known" in data

    def test_authentication_required(self, client, test_vocabulary_words):
        """Test that authentication is required for vocabulary endpoints"""
        # Test without authentication
        response = client.get("/vocabulary/search", params={"query": "test"})
        assert response.status_code == 401

        response = client.get("/vocabulary/level/A1")
        assert response.status_code == 401

        response = client.post("/vocabulary/mark", json={"vocabulary_id": 1, "is_known": True})
        assert response.status_code == 401


@pytest.mark.performance
@pytest.mark.integration
class TestVocabularyPerformance:
    """Performance tests for vocabulary operations"""

    async def test_search_performance(self, db_session: Session, test_data_builder, performance_timer):
        """Test search performance with large dataset"""
        # Create large vocabulary dataset
        for i in range(1000):
            test_data_builder.create_vocabulary_word(
                word=f"word_{i}", lemma=f"lemma_{i}", difficulty_level="A1", frequency_rank=i
            )

        vocabulary_repository = VocabularyRepositorySync()
        progress_repository = UserVocabularyProgressRepository()
        vocabulary_service = VocabularyService(vocabulary_repository, progress_repository)

        # Test search performance
        performance_timer.start()
        results = await vocabulary_service.search_words(db_session, "word", limit=50)
        performance_timer.stop()

        assert len(results) == 50
        assert performance_timer.elapsed < 1.0  # Should complete within 1 second

    async def test_bulk_operations_performance(
        self, db_session: Session, test_user, test_data_builder, performance_timer
    ):
        """Test bulk operations performance"""
        # Create vocabulary words
        words = []
        for i in range(100):
            word = test_data_builder.create_vocabulary_word(
                word=f"bulk_word_{i}", lemma=f"bulk_lemma_{i}", difficulty_level="A1"
            )
            words.append(word)

        vocabulary_repository = VocabularyRepositorySync()
        progress_repository = UserVocabularyProgressRepository()
        vocabulary_service = VocabularyService(vocabulary_repository, progress_repository)

        # Test bulk marking performance
        word_ids = [word.id for word in words]
        request = BulkMarkWordsRequest(vocabulary_ids=word_ids, is_known=True)

        performance_timer.start()
        progress_list = await vocabulary_service.bulk_mark_words(db_session, test_user.id, request)
        performance_timer.stop()

        assert len(progress_list) == 100
        assert performance_timer.elapsed < 5.0  # Should complete within 5 seconds
