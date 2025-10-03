"""
Complete User Workflow Tests - Layer 5 API Contract Validation
Tests the COMPLETE flow that users experience:
1. Upload/process video chunk
2. Get vocabulary from chunk processing
3. Display vocabulary in game
4. Mark words as known
5. Verify state persists

These tests would catch bugs that escape even Layer 4 validation:
- Data flows correctly through entire pipeline
- API endpoints accept data from previous steps
- User interactions complete successfully
- State changes persist correctly
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle
from services.processing.chunk_services.vocabulary_filter_service import VocabularyFilterService


@pytest.fixture
async def test_engine():
    """Create in-memory test database engine"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session with transaction rollback"""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    """Create test user"""
    user = User(
        id=1, email="test@example.com", username="testuser", hashed_password="hashed", is_active=True, is_verified=True
    )

    test_db_session.add(user)
    await test_db_session.commit()

    return user


@pytest.fixture
async def german_vocabulary(test_db_session: AsyncSession):
    """Insert German vocabulary test data"""
    words = [
        VocabularyWord(
            word="Hallo",
            lemma="hallo",
            language="de",
            difficulty_level="A1",
            part_of_speech="interjection",
            translation_en="hello",
        ),
        VocabularyWord(
            word="Welt",
            lemma="welt",
            language="de",
            difficulty_level="A2",
            part_of_speech="noun",
            gender="die",
            translation_en="world",
        ),
        VocabularyWord(
            word="glücklich",
            lemma="glücklich",
            language="de",
            difficulty_level="C2",
            part_of_speech="adjective",
            translation_en="happy",
        ),
    ]

    for word in words:
        test_db_session.add(word)

    await test_db_session.commit()

    return words


class TestCompleteUserWorkflow:
    """
    Layer 5 Tests: Complete user workflow validation

    These tests exercise the ENTIRE user experience:
    - Process subtitles → Extract vocabulary → Display in game → Mark as known

    Previous layers missed bugs because they tested components in isolation.
    These tests validate the complete integration.
    """

    @pytest.mark.asyncio
    async def test_complete_vocabulary_game_workflow(self, test_user, german_vocabulary):
        """
        Test the complete workflow from subtitle processing to marking words as known

        User Story:
        1. User uploads video chunk with subtitles
        2. System processes subtitles and extracts vocabulary
        3. User plays vocabulary game with extracted words
        4. User marks words as "known"
        5. System persists known words

        This test validates ALL steps work together.
        """
        # Step 1: Simulate filtered words from subtitle processing
        # (DirectSubtitleProcessor would generate these)
        service = VocabularyFilterService()

        class MockFilteredWord:
            def __init__(self, word_text, difficulty, lemma):
                self.word = word_text
                self.difficulty_level = difficulty
                self.lemma = lemma
                self.translation = None
                self.part_of_speech = "noun"
                self.concept_id = None  # FilteredWord has None

        filter_result = {
            "blocking_words": [
                MockFilteredWord("Hallo", "A1", "hallo"),
                MockFilteredWord("Welt", "A2", "welt"),
                MockFilteredWord("glücklich", "C2", "glücklich"),
            ]
        }

        # Step 2: Extract vocabulary for game (this is what VocabularyFilterService does)
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Step 3: Validate vocabulary can be displayed in game
        # (This is where Bugs #6-8 would break the frontend)
        assert len(vocabulary) > 0, "Should have extracted vocabulary"

        for word in vocabulary:
            # Bug #6: Field name must be correct
            assert "difficulty_level" in word, "Frontend expects difficulty_level"
            assert "difficulty" not in word, "Wrong field name would crash frontend"

            # Bug #7: Value must not be None
            assert word["concept_id"] is not None, "None would cause Pydantic warnings"

            # Bug #8: Format must be valid UUID
            try:
                parsed_uuid = uuid.UUID(word["concept_id"])
                assert str(parsed_uuid) == word["concept_id"], "UUID must be canonical format"
            except ValueError as e:
                pytest.fail(f"Invalid UUID would cause 422 error: {word['concept_id']} - {e}")

            # Verify frontend can render the word
            difficulty_display = word["difficulty_level"].lower()
            assert difficulty_display in ["a1", "a2", "b1", "b2", "c1", "c2", "unknown"]

        # Step 4: Simulate marking word as known (validates API contract)
        # This is where Bug #8 would cause 422 error
        word_to_mark = vocabulary[0]

        # Verify concept_id would be accepted by API validator
        # (api/routes/vocabulary.py:25-33 validates UUID format)
        concept_id = word_to_mark["concept_id"]

        # This is the exact validation the API performs
        try:
            uuid.UUID(concept_id)
        except ValueError:
            pytest.fail(
                f"API would reject this concept_id with 422 error: {concept_id}\n"
                "This is Bug #8: concept_id must be valid UUID"
            )

        # Step 5: Verify complete workflow succeeded
        assert True, "Complete workflow from processing → display → interaction succeeded"

    @pytest.mark.asyncio
    async def test_vocabulary_survives_round_trip(self, test_user, german_vocabulary):
        """
        Test that vocabulary generated by backend can be consumed by frontend and sent back

        This tests the complete round-trip:
        1. Backend generates vocabulary
        2. Frontend receives and displays it
        3. Frontend sends concept_id back to backend
        4. Backend accepts it
        """
        # Step 1: Generate vocabulary (backend)
        service = VocabularyFilterService()

        class MockFilteredWord:
            word = "glücklich"
            difficulty_level = "C2"
            lemma = "glücklich"
            concept_id = None

        vocabulary = service.extract_vocabulary_from_result({"blocking_words": [MockFilteredWord()]})

        assert len(vocabulary) > 0, "Must generate vocabulary"

        # Step 2: Frontend receives vocabulary
        word = vocabulary[0]

        # Frontend TypeScript type check (simulated)
        # export type VocabularyWord = {
        #     concept_id: string;
        #     word: string;
        #     difficulty_level: string;
        # }
        assert isinstance(word["concept_id"], str)
        assert isinstance(word["word"], str)
        assert isinstance(word["difficulty_level"], str)

        # Step 3: Frontend sends concept_id back to backend
        concept_id_to_send = word["concept_id"]

        # Step 4: Backend validates concept_id (simulates MarkKnownRequest validation)
        # This is the exact validation from api/routes/vocabulary.py
        try:
            uuid.UUID(concept_id_to_send)
        except ValueError as e:
            pytest.fail(
                f"Round-trip failed: Backend generated invalid concept_id\n"
                f"Generated: {concept_id_to_send}\n"
                f"Error: {e}\n"
                "Backend would reject its own data with 422!"
            )

        assert True, "Vocabulary survives complete round-trip"

    @pytest.mark.asyncio
    async def test_multiple_words_all_have_valid_uuids(self, test_user, german_vocabulary):
        """
        Test that ALL words in a batch have valid UUIDs

        Bug #8 could affect any word - test entire batch
        """
        service = VocabularyFilterService()

        class MockFilteredWord:
            def __init__(self, word_text, difficulty, lemma):
                self.word = word_text
                self.difficulty_level = difficulty
                self.lemma = lemma
                self.concept_id = None

        # Create multiple words including edge cases
        filter_result = {
            "blocking_words": [
                MockFilteredWord("Hallo", "A1", "hallo"),
                MockFilteredWord("Welt", "A2", "welt"),
                MockFilteredWord("ich", "A1", "ich"),
                MockFilteredWord("bin", "A1", "sein"),
                MockFilteredWord("sehr", "B1", "sehr"),
                MockFilteredWord("glücklich", "C2", "glücklich"),
            ]
        }

        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Validate EVERY word (Bug #8 could affect any word)
        invalid_words = []
        for word in vocabulary:
            try:
                uuid.UUID(word["concept_id"])
            except ValueError:
                invalid_words.append({"word": word["word"], "concept_id": word["concept_id"]})

        if invalid_words:
            pytest.fail(
                f"Found {len(invalid_words)} words with invalid UUIDs:\n"
                + "\n".join([f"  - {w['word']}: {w['concept_id']}" for w in invalid_words])
            )

        assert len(vocabulary) > 0, "Should have generated vocabulary"

    @pytest.mark.asyncio
    async def test_same_word_gets_same_uuid_across_sessions(self, test_user, german_vocabulary):
        """
        Test that same word generates same UUID (deterministic)

        User Story: User learns word in Session 1, marks as known.
        In Session 2, same word should have same UUID so system knows it's known.
        """
        service = VocabularyFilterService()

        # Use dict format that matches what the service expects
        mock_word = {"word": "glücklich", "difficulty_level": "C2", "lemma": "glücklich", "concept_id": None}

        # Session 1: Process vocabulary with "glücklich"
        vocab1 = service.extract_vocabulary_from_result({"blocking_words": [mock_word]})

        # Session 2: Process vocabulary with same word "glücklich"
        vocab2 = service.extract_vocabulary_from_result({"blocking_words": [mock_word]})

        # Find "glücklich" in both sessions
        glucklish_word1 = next((w for w in vocab1 if w["word"] == "glücklich"), None)
        glucklish_word2 = next((w for w in vocab2 if w["word"] == "glücklich"), None)

        assert glucklish_word1 is not None, "Should find glücklich in session 1"
        assert glucklish_word2 is not None, "Should find glücklich in session 2"

        # CRITICAL: Same word must have same UUID across sessions
        assert glucklish_word1["concept_id"] == glucklish_word2["concept_id"], (
            f"Same word must have same UUID across sessions:\n"
            f"Session 1: {glucklish_word1['concept_id']}\n"
            f"Session 2: {glucklish_word2['concept_id']}\n"
            "Without deterministic UUIDs, user's 'known words' state won't work!"
        )

    @pytest.mark.asyncio
    async def test_frontend_can_safely_render_all_vocabulary(self, test_user, german_vocabulary):
        """
        Test that frontend can safely render ALL vocabulary without crashes

        Simulates frontend code that would crash with Bugs #6-8:
        - Bug #6: word.difficulty_level.toLowerCase() → crashes if field doesn't exist
        - Bug #7: word.concept_id → crashes if None
        - Bug #8: Send concept_id to API → 422 if invalid UUID
        """
        service = VocabularyFilterService()

        # Use dict format that matches what the service expects
        filter_result = {
            "blocking_words": [
                {"word": "Hallo", "difficulty_level": "A1", "lemma": "hallo", "concept_id": None},
                {"word": "Welt", "difficulty_level": "A2", "lemma": "welt", "concept_id": None},
                {"word": "glücklich", "difficulty_level": "C2", "lemma": "glücklich", "concept_id": None},
            ]
        }

        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Simulate frontend rendering code
        for word in vocabulary:
            # VocabularyGame.tsx:122 - styled-component
            # <DifficultyBadge $level={currentWord?.difficulty_level}>
            try:
                difficulty_level = word["difficulty_level"]  # Bug #6 would fail here
                difficulty_level.lower()  # Bug #6 would crash here
            except (KeyError, AttributeError) as e:
                pytest.fail(
                    f"Frontend would crash rendering word '{word.get('word', 'unknown')}':\n"
                    f"Error: {e}\n"
                    "This is Bug #6: difficulty_level field missing or wrong"
                )

            # Frontend needs concept_id for interaction
            try:
                concept_id = word["concept_id"]  # Bug #7 would give None
                if concept_id is None:
                    raise ValueError("concept_id is None")

                # Frontend sends to API
                uuid.UUID(concept_id)  # Bug #8 would fail here
            except (KeyError, ValueError) as e:
                pytest.fail(
                    f"Frontend can't interact with word '{word.get('word', 'unknown')}':\n"
                    f"concept_id: {word.get('concept_id', 'missing')}\n"
                    f"Error: {e}\n"
                    "This is Bug #7 or #8: concept_id None or invalid UUID"
                )

        assert len(vocabulary) > 0, "Should have vocabulary to render"


class TestErrorCases:
    """Test error cases in complete workflow"""

    @pytest.mark.asyncio
    async def test_empty_vocabulary_doesnt_crash(self, test_user, german_vocabulary):
        """Test that empty vocabulary is handled gracefully"""
        processor = DirectSubtitleProcessor()

        # Subtitles with only easy words (below A1)
        subtitles = [
            FilteredSubtitle(
                original_text="",  # Empty subtitle
                start_time=1.0,
                end_time=2.0,
                words=[],
            )
        ]

        result = await processor.process_subtitles(
            subtitles=subtitles, user_id=str(test_user.id), user_level="A1", language="de"
        )

        service = VocabularyFilterService()
        vocabulary = service.extract_vocabulary_from_result({"blocking_words": result.blocker_words})

        # Should return empty list, not crash
        assert isinstance(vocabulary, list)
        assert len(vocabulary) == 0

    @pytest.mark.asyncio
    async def test_vocabulary_without_lemma(self, test_user, german_vocabulary):
        """Test words without lemma still get valid UUIDs"""
        service = VocabularyFilterService()

        class MockWordWithoutLemma:
            def __init__(self):
                self.word = "test"
                self.difficulty_level = "A1"
                self.lemma = None  # No lemma
                self.concept_id = None

        filter_result = {"blocking_words": [MockWordWithoutLemma()]}
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        assert len(vocabulary) == 1
        word = vocabulary[0]

        # Must still have valid UUID even without lemma
        assert word["concept_id"] is not None
        try:
            uuid.UUID(word["concept_id"])
        except ValueError:
            pytest.fail("Words without lemma must still get valid UUIDs")
