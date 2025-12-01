"""
Integration tests for VocabularyService with real database operations
Tests actual service methods with database interactions
"""

import pytest
from sqlalchemy import and_, select

from database.models import User, UserVocabularyProgress, VocabularyWord
from services.vocabulary.vocabulary_service import VocabularyService


class TestVocabularyServiceDatabaseIntegration:
    """Integration tests for VocabularyService with real database"""

    @pytest.fixture
    async def db_session(self, app):
        """Get database session from app"""
        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            yield session

    @pytest.fixture
    async def vocabulary_service(self):
        """Create vocabulary service instance"""
        from services.vocabulary.vocabulary_progress_service import get_vocabulary_progress_service
        from services.vocabulary.vocabulary_query_service import get_vocabulary_query_service
        from services.vocabulary.vocabulary_stats_service import get_vocabulary_stats_service

        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        return VocabularyService(query_service, progress_service, stats_service)

    @pytest.fixture
    async def test_user(self, db_session):
        """Create test user"""
        user = User(email="vocabtest@example.com", username="vocabtest", hashed_password="hashed", is_active=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_vocabulary(self, db_session):
        """Create test vocabulary words"""
        words = [
            VocabularyWord(
                lemma="Haus",
                word="das Haus",
                language="de",
                difficulty_level="A1",
                part_of_speech="noun",
                gender="das",
                translation_en="house",
            ),
            VocabularyWord(
                lemma="laufen",
                word="laufen",
                language="de",
                difficulty_level="A2",
                part_of_speech="verb",
                translation_en="to run",
            ),
            VocabularyWord(
                lemma="schnell",
                word="schnell",
                language="de",
                difficulty_level="A2",
                part_of_speech="adjective",
                translation_en="fast",
            ),
        ]

        for word in words:
            db_session.add(word)

        await db_session.commit()

        for word in words:
            await db_session.refresh(word)

        return words

    async def test_get_word_info_found(self, vocabulary_service, db_session, test_vocabulary):
        """Test getting word info for existing word"""
        # Act
        result = await vocabulary_service.get_word_info("Haus", "de", db_session)

        # Assert
        assert result["found"] is True
        assert result["lemma"] == "Haus"
        assert result["found_word"] == "das Haus"
        assert result["difficulty_level"] == "A1"
        assert result["translation_en"] == "house"

    async def test_get_word_info_not_found(self, vocabulary_service, db_session, test_vocabulary):
        """Test getting word info for non-existent word"""
        # Act
        result = await vocabulary_service.get_word_info("nonexistent", "de", db_session)

        # Assert
        assert result["found"] is False
        assert result["word"] == "nonexistent"
        assert "message" in result

    async def test_mark_word_known_success(self, vocabulary_service, db_session, test_user, test_vocabulary):
        """Test marking word as known"""
        # Act
        result = await vocabulary_service.mark_word_known(test_user.id, "Haus", "de", True, db_session)

        # Assert
        assert result["success"] is True
        assert result["is_known"] is True
        assert result["lemma"] == "Haus"

        # Verify database state
        stmt = select(UserVocabularyProgress).where(UserVocabularyProgress.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        progress = db_result.scalar_one()

        assert progress.is_known is True
        assert progress.lemma == "Haus"

    async def test_mark_word_known_word_not_found(self, vocabulary_service, db_session, test_user, test_vocabulary):
        """Test marking non-existent word as known (supports unknown words with lemmatization)"""
        # Act
        result = await vocabulary_service.mark_word_known(test_user.id, "nonexistent", "de", True, db_session)

        # Assert - New behavior: allows marking unknown words as known
        assert result["success"] is True
        assert result["word"] == "nonexistent"
        assert result["is_known"] is True
        assert result["level"] == "unknown"  # No CEFR level for unknown words

        # Verify database state - word should be marked with vocabulary_id=NULL
        stmt = select(UserVocabularyProgress).where(
            and_(UserVocabularyProgress.user_id == test_user.id, UserVocabularyProgress.lemma == result["lemma"])
        )
        db_result = await db_session.execute(stmt)
        progress = db_result.scalar_one()

        assert progress.is_known is True
        assert progress.vocabulary_id is None  # Unknown word - no vocabulary_id

    async def test_mark_word_known_toggle(self, vocabulary_service, db_session, test_user, test_vocabulary):
        """Test toggling word known status"""
        # Mark as known
        await vocabulary_service.mark_word_known(test_user.id, "laufen", "de", True, db_session)

        # Mark as unknown
        result = await vocabulary_service.mark_word_known(test_user.id, "laufen", "de", False, db_session)

        # Assert
        assert result["success"] is True

        # Verify final state
        stmt = select(UserVocabularyProgress).where(UserVocabularyProgress.user_id == test_user.id)
        db_result = await db_session.execute(stmt)
        progress = db_result.scalar_one()

        assert progress.is_known is False

    async def test_get_word_info_case_insensitive(self, vocabulary_service, db_session, test_vocabulary):
        """Test word lookup is case-insensitive"""
        # Test with lowercase
        result1 = await vocabulary_service.get_word_info("haus", "de", db_session)
        assert result1["found"] is True

        # Test with uppercase
        result2 = await vocabulary_service.get_word_info("HAUS", "de", db_session)
        assert result2["found"] is True

        # Both should find the same word
        assert result1["lemma"] == result2["lemma"]

    async def test_multiple_users_independent_progress(self, vocabulary_service, db_session, test_vocabulary):
        """Test that multiple users have independent progress"""
        # Create two users
        user1 = User(email="user1@example.com", username="user1", hashed_password="hashed", is_active=True)
        user2 = User(email="user2@example.com", username="user2", hashed_password="hashed", is_active=True)
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        # User 1 marks word as known
        await vocabulary_service.mark_word_known(user1.id, "schnell", "de", True, db_session)

        # User 2 marks word as unknown
        await vocabulary_service.mark_word_known(user2.id, "schnell", "de", False, db_session)

        # Verify independent progress
        stmt1 = select(UserVocabularyProgress).where(UserVocabularyProgress.user_id == user1.id)
        result1 = await db_session.execute(stmt1)
        progress1 = result1.scalar_one()

        stmt2 = select(UserVocabularyProgress).where(UserVocabularyProgress.user_id == user2.id)
        result2 = await db_session.execute(stmt2)
        progress2 = result2.scalar_one()

        assert progress1.is_known is True
        assert progress2.is_known is False
