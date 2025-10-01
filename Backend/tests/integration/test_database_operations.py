"""
Integration tests for database operations
Tests actual database operations with real database (no mocking)
"""

import pytest
from sqlalchemy import and_, func, select

from core.auth import User
from database.models import UserVocabularyProgress, VocabularyWord


class TestVocabularyDatabaseOperations:
    """Integration tests for vocabulary database operations"""

    @pytest.fixture
    async def db_session(self, app):
        """Get database session from app"""
        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            yield session

    @pytest.fixture
    async def test_vocabulary_data(self, db_session):
        """Create test vocabulary data"""
        words = [
            VocabularyWord(lemma="house", word="house", language="en", difficulty_level="A1", part_of_speech="noun"),
            VocabularyWord(lemma="Haus", word="Haus", language="de", difficulty_level="A1", part_of_speech="noun"),
            VocabularyWord(
                lemma="Katze", word="die Katze", language="de", difficulty_level="A2", part_of_speech="noun"
            ),
        ]

        for word in words:
            db_session.add(word)

        await db_session.commit()

        # Refresh to get IDs
        for word in words:
            await db_session.refresh(word)

        return words

    async def test_create_vocabulary_word(self, db_session):
        """Test creating a new vocabulary word"""
        # Arrange
        word = VocabularyWord(lemma="test", word="test", language="en", difficulty_level="B1", part_of_speech="noun")

        # Act
        db_session.add(word)
        await db_session.commit()
        await db_session.refresh(word)

        # Assert
        assert word.id is not None
        assert word.lemma == "test"
        assert word.difficulty_level == "B1"

    async def test_query_by_language(self, db_session, test_vocabulary_data):
        """Test querying words by language"""
        # Act
        stmt = select(VocabularyWord).where(VocabularyWord.language == "de")
        result = await db_session.execute(stmt)
        words = result.scalars().all()

        # Assert
        assert len(words) == 2  # Haus and Katze
        assert all(w.language == "de" for w in words)

    async def test_query_by_level(self, db_session, test_vocabulary_data):
        """Test querying words by difficulty level"""
        # Act
        stmt = select(VocabularyWord).where(VocabularyWord.difficulty_level == "A1")
        result = await db_session.execute(stmt)
        words = result.scalars().all()

        # Assert
        assert len(words) == 2  # house and Haus
        assert all(w.difficulty_level == "A1" for w in words)

    async def test_query_by_lemma(self, db_session, test_vocabulary_data):
        """Test querying word by lemma"""
        # Act
        stmt = select(VocabularyWord).where(VocabularyWord.lemma == "Haus")
        result = await db_session.execute(stmt)
        word = result.scalar_one_or_none()

        # Assert
        assert word is not None
        assert word.lemma == "Haus"
        assert word.word == "Haus"

    async def test_count_by_level(self, db_session, test_vocabulary_data):
        """Test counting words by level"""
        # Act
        stmt = select(func.count(VocabularyWord.id)).where(VocabularyWord.difficulty_level == "A1")
        result = await db_session.execute(stmt)
        count = result.scalar()

        # Assert
        assert count == 2

    async def test_update_vocabulary_word(self, db_session, test_vocabulary_data):
        """Test updating a vocabulary word"""
        # Arrange
        word_to_update = test_vocabulary_data[0]

        # Act
        stmt = select(VocabularyWord).where(VocabularyWord.id == word_to_update.id)
        result = await db_session.execute(stmt)
        word = result.scalar_one()

        word.difficulty_level = "B2"
        await db_session.commit()
        await db_session.refresh(word)

        # Assert
        assert word.difficulty_level == "B2"

    async def test_delete_vocabulary_word(self, db_session, test_vocabulary_data):
        """Test deleting a vocabulary word"""
        # Arrange
        word_to_delete = test_vocabulary_data[0]

        # Act
        stmt = select(VocabularyWord).where(VocabularyWord.id == word_to_delete.id)
        result = await db_session.execute(stmt)
        word = result.scalar_one()

        await db_session.delete(word)
        await db_session.commit()

        # Verify deletion
        result = await db_session.execute(stmt)
        deleted_word = result.scalar_one_or_none()

        # Assert
        assert deleted_word is None

    async def test_complex_query_with_multiple_conditions(self, db_session, test_vocabulary_data):
        """Test complex query with AND conditions"""
        # Act
        stmt = select(VocabularyWord).where(
            and_(VocabularyWord.language == "de", VocabularyWord.difficulty_level == "A1")
        )
        result = await db_session.execute(stmt)
        words = result.scalars().all()

        # Assert
        assert len(words) == 1  # Only Haus
        assert words[0].lemma == "Haus"


class TestUserDatabaseOperations:
    """Integration tests for user database operations"""

    @pytest.fixture
    async def db_session(self, app):
        """Get database session from app"""
        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            yield session

    async def test_create_user(self, db_session):
        """Test creating a new user"""
        # Arrange
        user = User(
            email="test@example.com", username="testuser", hashed_password="hashed_password_123", is_active=True
        )

        # Act
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Assert
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True

    async def test_query_user_by_email(self, db_session):
        """Test querying user by email"""
        # Arrange
        user = User(email="query@example.com", username="queryuser", hashed_password="hashed", is_active=True)
        db_session.add(user)
        await db_session.commit()

        # Act
        stmt = select(User).where(User.email == "query@example.com")
        result = await db_session.execute(stmt)
        found_user = result.scalar_one_or_none()

        # Assert
        assert found_user is not None
        assert found_user.email == "query@example.com"

    async def test_update_user(self, db_session):
        """Test updating user data"""
        # Arrange
        user = User(email="update@example.com", username="updateuser", hashed_password="hashed", is_active=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Act
        stmt = select(User).where(User.id == user.id)
        result = await db_session.execute(stmt)
        user_to_update = result.scalar_one()

        user_to_update.is_active = False
        await db_session.commit()
        await db_session.refresh(user_to_update)

        # Assert
        assert user_to_update.is_active is False

    async def test_user_unique_email_constraint(self, db_session):
        """Test that email must be unique"""
        # Arrange
        user1 = User(email="duplicate@example.com", username="duplicate1", hashed_password="hashed1", is_active=True)
        db_session.add(user1)
        await db_session.commit()

        # Act & Assert
        user2 = User(email="duplicate@example.com", username="duplicate2", hashed_password="hashed2", is_active=True)
        db_session.add(user2)

        # Should raise integrity error on commit
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await db_session.commit()


class TestUserVocabularyProgressOperations:
    """Integration tests for user vocabulary progress"""

    @pytest.fixture
    async def db_session(self, app):
        """Get database session from app"""
        SessionLocal = app.state._test_session_factory
        async with SessionLocal() as session:
            yield session

    @pytest.fixture
    async def test_user_and_vocab(self, db_session):
        """Create test user and vocabulary"""
        user = User(email="progress@example.com", username="progressuser", hashed_password="hashed", is_active=True)
        db_session.add(user)

        word = VocabularyWord(lemma="test", word="test", language="en", difficulty_level="A1", part_of_speech="noun")
        db_session.add(word)

        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(word)

        return user, word

    async def test_create_progress_record(self, db_session, test_user_and_vocab):
        """Test creating user vocabulary progress"""
        # Arrange
        user, word = test_user_and_vocab

        progress = UserVocabularyProgress(
            user_id=user.id,
            vocabulary_id=word.id,
            lemma=word.lemma,
            language=word.language,
            is_known=True,
            confidence_level=3,
        )

        # Act
        db_session.add(progress)
        await db_session.commit()
        await db_session.refresh(progress)

        # Assert
        assert progress.id is not None
        assert progress.is_known is True
        assert progress.confidence_level == 3

    async def test_query_user_known_words(self, db_session, test_user_and_vocab):
        """Test querying user's known words"""
        # Arrange
        user, word = test_user_and_vocab

        progress = UserVocabularyProgress(
            user_id=user.id,
            vocabulary_id=word.id,
            lemma=word.lemma,
            language=word.language,
            is_known=True,
            confidence_level=3,
        )
        db_session.add(progress)
        await db_session.commit()

        # Act
        stmt = select(UserVocabularyProgress).where(
            and_(UserVocabularyProgress.user_id == user.id, UserVocabularyProgress.is_known)
        )
        result = await db_session.execute(stmt)
        known_words = result.scalars().all()

        # Assert
        assert len(known_words) == 1
        assert known_words[0].lemma == "test"

    async def test_update_progress_confidence(self, db_session, test_user_and_vocab):
        """Test updating confidence level"""
        # Arrange
        user, word = test_user_and_vocab

        progress = UserVocabularyProgress(
            user_id=user.id,
            vocabulary_id=word.id,
            lemma=word.lemma,
            language=word.language,
            is_known=True,
            confidence_level=1,
        )
        db_session.add(progress)
        await db_session.commit()
        await db_session.refresh(progress)

        # Act
        stmt = select(UserVocabularyProgress).where(UserVocabularyProgress.id == progress.id)
        result = await db_session.execute(stmt)
        progress_to_update = result.scalar_one()

        progress_to_update.confidence_level = 5
        await db_session.commit()
        await db_session.refresh(progress_to_update)

        # Assert
        assert progress_to_update.confidence_level == 5
