"""
TRUE End-to-End API Contract Validation Tests

Tests that backend responses match frontend type expectations.
This would have caught Bug #6: difficulty vs difficulty_level
And Bug #7: concept_id must be valid UUID

AI/ML Dependency: spaCy German Language Model
---------------------------------------------
Two tests in this suite require the spaCy 'de_core_news_lg' German language model
for vocabulary extraction and lemmatization. These tests are skipped in CI environments.

To run all tests locally:
    pip install spacy
    python -m spacy download de_core_news_lg

The spaCy model is used for:
- German word lemmatization
- Part-of-speech tagging
- Vocabulary level detection
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, User, VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle, FilteredWord
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
    """Create test database session"""
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
            word="ist", lemma="sein", language="de", difficulty_level="A1", part_of_speech="verb", translation_en="is"
        ),
    ]

    for word in words:
        test_db_session.add(word)

    await test_db_session.commit()

    return words


class TestFrontendBackendContract:
    """Test that backend responses match frontend type expectations"""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires spaCy de_core_news_lg model (python -m spacy download de_core_news_lg)")
    async def test_vocabulary_response_matches_frontend_type(self, german_vocabulary):
        """
        Test that vocabulary response has ALL required fields for frontend VocabularyWord type
        This test reproduces Bug #6: difficulty vs difficulty_level mismatch
        """
        # Create processor
        processor = DirectSubtitleProcessor()

        # Create sample subtitles
        subtitles = [
            FilteredSubtitle(
                original_text="Hallo Welt",
                start_time=1.0,
                end_time=3.0,
                words=[
                    FilteredWord(text="Hallo", start_time=1.0, end_time=1.5),
                    FilteredWord(text="Welt", start_time=1.5, end_time=3.0),
                ],
            )
        ]

        # Process subtitles
        result = await processor.process_subtitles(
            subtitles=subtitles, user_id="test_user", user_level="A1", language="de"
        )

        # Get blocking words (vocabulary for game)
        blocking_words = result.statistics.get("blocking_words") or []

        # Frontend expects VocabularyWord with these REQUIRED fields:
        required_fields = ["concept_id", "word", "difficulty_level"]

        # Optional fields that should be present or null
        optional_fields = ["translation", "lemma", "semantic_category", "domain"]

        for word in blocking_words:
            # Verify all REQUIRED fields exist
            for field in required_fields:
                assert field in word, f"Missing required field '{field}' in vocabulary word: {word}"
                assert word[field] is not None, f"Required field '{field}' is None in vocabulary word: {word}"

            # Verify NO WRONG fields (like "difficulty" instead of "difficulty_level")
            assert "difficulty" not in word, "Found wrong field 'difficulty' - should be 'difficulty_level'"

            # Verify optional fields are present (can be None)
            for field in optional_fields:
                assert field in word, f"Missing optional field '{field}' in vocabulary word: {word}"

    @pytest.mark.asyncio
    async def test_vocabulary_filter_service_response_contract(self, test_user, german_vocabulary):
        """
        Test that VocabularyFilterService returns correct structure
        This is the service that creates vocabulary for chunk processing
        """
        service = VocabularyFilterService()

        # Create mock filter result (simulates subtitle processor output)
        class MockWord:
            def __init__(self, word_text, difficulty, lemma=None, translation=None):
                self.word = word_text
                self.difficulty_level = difficulty
                self.lemma = lemma
                self.translation = translation
                self.part_of_speech = "noun"
                self.concept_id = f"concept_{word_text}"

        filter_result = {
            "blocking_words": [
                MockWord("Hallo", "A1", "hallo", "hello"),
                MockWord("Welt", "A2", "welt", "world"),
            ]
        }

        # Extract vocabulary
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Verify response structure matches frontend expectations
        assert len(vocabulary) == 2

        for vocab_word in vocabulary:
            # Required fields (frontend expects these to be non-null)
            assert "concept_id" in vocab_word
            assert vocab_word["concept_id"] is not None

            assert "word" in vocab_word
            assert vocab_word["word"] is not None

            assert "difficulty_level" in vocab_word  # NOT "difficulty"!
            assert vocab_word["difficulty_level"] is not None

            # Optional fields (can be null but must exist)
            assert "translation" in vocab_word
            assert "lemma" in vocab_word
            assert "semantic_category" in vocab_word
            assert "domain" in vocab_word

            # Verify NO wrong field names
            assert "difficulty" not in vocab_word, "Field should be 'difficulty_level' not 'difficulty'"

    def test_bug_6_difficulty_vs_difficulty_level(self):
        """
        Reproduce Bug #6: Backend returned "difficulty" but frontend expected "difficulty_level"
        This test would have failed before the fix
        """
        service = VocabularyFilterService()

        # Use dict format that matches what the service expects
        filter_result = {"blocking_words": [{"word": "test", "difficulty_level": "A1", "lemma": "test"}]}

        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # This assertion would FAIL with the buggy code that used "difficulty"
        assert (
            "difficulty_level" in vocabulary[0]
        ), "Response must have 'difficulty_level' field to match frontend VocabularyWord type"

        # This assertion catches the bug
        assert (
            "difficulty" not in vocabulary[0]
        ), "Response must NOT have 'difficulty' field - frontend expects 'difficulty_level'"

        # Verify the value is correctly set
        assert vocabulary[0]["difficulty_level"] == "A1"


class TestAPIContractValidation:
    """Test that API responses match generated TypeScript types"""

    @pytest.mark.asyncio
    async def test_vocabulary_word_matches_typescript_interface(self):
        """
        Verify vocabulary word structure matches frontend TypeScript interface:

        export type VocabularyWord = {
            concept_id: string;
            word: string;
            translation?: string | null;
            lemma?: string | null;
            difficulty_level: string;  // REQUIRED, not optional!
            semantic_category?: string | null;
            domain?: string | null;
        }
        """
        service = VocabularyFilterService()

        # Use dict format that matches what the service expects
        filter_result = {
            "blocking_words": [
                {
                    "word": "Haus",
                    "difficulty_level": "A1",
                    "lemma": "haus",
                    "translation": "house",
                    "concept_id": None,  # Service will generate UUID
                }
            ]
        }
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        word = vocabulary[0]

        # Required fields (match TypeScript non-optional fields)
        # concept_id must be valid UUID (not hardcoded value)
        assert word["concept_id"] is not None
        assert isinstance(word["concept_id"], str)
        # Verify it's a valid UUID format (Bug #8 fix)
        try:
            uuid.UUID(word["concept_id"])
        except ValueError:
            pytest.fail(f"concept_id '{word['concept_id']}' is not a valid UUID")

        assert word["word"] == "Haus"
        assert word["difficulty_level"] == "A1"

        # Optional fields (match TypeScript optional fields)
        assert "translation" in word  # Can be null but must exist
        assert "lemma" in word
        assert "semantic_category" in word
        assert "domain" in word

        # Type correctness
        assert isinstance(word["word"], str)
        assert isinstance(word["difficulty_level"], str)

    def test_difficulty_level_field_contract(self):
        """
        Test that vocabulary words always have difficulty_level field
        This prevents the error the user experienced: "Cannot read properties of undefined (reading 'toLowerCase')"
        """
        service = VocabularyFilterService()

        class MockWord:
            def __init__(self):
                self.word = "test"
                self.difficulty_level = "A1"

        filter_result = {"blocking_words": [MockWord()]}
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Verify difficulty_level exists and is valid
        word = vocabulary[0]
        assert "difficulty_level" in word
        assert word["difficulty_level"] is not None
        assert isinstance(word["difficulty_level"], str)
        assert len(word["difficulty_level"]) > 0

        # Verify it can be used in lowercase operations (like styled-components)
        assert word["difficulty_level"].lower() in ["a1", "a2", "b1", "b2", "c1", "c2", "unknown"]


class TestEndToEndContractValidation:
    """
    End-to-end tests that validate complete request/response cycles
    These tests exercise actual code paths and validate data contracts
    """

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires spaCy de_core_news_lg model (python -m spacy download de_core_news_lg)")
    async def test_chunk_processing_vocabulary_contract(self, test_user, german_vocabulary):
        """
        Test the complete flow from subtitle processing to vocabulary extraction
        Validates that the data structure at each step matches expectations
        """
        # Step 1: Process subtitles
        processor = DirectSubtitleProcessor()
        subtitles = [
            FilteredSubtitle(
                original_text="Hallo Welt",
                start_time=1.0,
                end_time=3.0,
                words=[
                    FilteredWord(text="Hallo", start_time=1.0, end_time=1.5),
                    FilteredWord(text="Welt", start_time=1.5, end_time=3.0),
                ],
            )
        ]

        result = await processor.process_subtitles(
            subtitles=subtitles, user_id="test_user", user_level="A1", language="de"
        )

        # Step 2: Extract vocabulary using filter service
        service = VocabularyFilterService()

        # Simulate the filter result structure
        filter_result = {"blocking_words": result.blocker_words}

        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Step 3: Validate vocabulary matches frontend contract
        if vocabulary:  # Only validate if we have vocabulary
            for word in vocabulary:
                # All required fields must exist and be non-null
                assert word.get("concept_id"), "concept_id is required"
                assert word.get("word"), "word is required"
                assert word.get("difficulty_level"), "difficulty_level is required"

                # Field names must match TypeScript interface exactly
                assert "difficulty_level" in word
                assert "difficulty" not in word  # Common mistake!

                # Types must be correct
                assert isinstance(word["concept_id"], str)
                assert isinstance(word["word"], str)
                assert isinstance(word["difficulty_level"], str)


class TestUUIDValidation:
    """
    Tests that validate concept_id is always a valid UUID
    These tests would have caught Bugs #7 and #8
    """

    def test_bug_7_concept_id_never_none(self):
        """
        Bug #7: Pydantic serialization warnings about concept_id being None

        Reproduce the bug:
        - FilteredWord objects have concept_id = None
        - Old code: getattr(word, "concept_id", f"word_{word.word}")
        - When concept_id exists but is None, getattr returns None (not the fallback!)
        - Result: Pydantic warnings and frontend errors

        This test would have FAILED with the buggy code.
        """
        service = VocabularyFilterService()

        class MockWord:
            def __init__(self):
                self.word = "glücklich"
                self.difficulty_level = "C2"
                self.lemma = "glücklich"
                self.concept_id = None  # Simulates FilteredWord that has None concept_id

        filter_result = {"blocking_words": [MockWord()]}
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        word = vocabulary[0]

        # Bug #7: This assertion would FAIL with buggy code (concept_id would be None)
        assert word["concept_id"] is not None, "Bug #7: concept_id is None - causes Pydantic serialization warnings"

        # Verify it's a non-empty string
        assert isinstance(word["concept_id"], str)
        assert len(word["concept_id"]) > 0

    def test_bug_8_concept_id_is_valid_uuid(self):
        """
        Bug #8: UUID validation error when marking words as known

        Reproduce the bug:
        - Frontend sends concept_id to POST /api/vocabulary/mark-known
        - API expects valid UUID format (validated in vocabulary.py:25-33)
        - Old code generated: "glücklich-C2" or "word_glücklich"
        - Result: 422 Unprocessable Content error

        This test would have FAILED with the buggy code.
        """
        service = VocabularyFilterService()

        class MockWord:
            def __init__(self):
                self.word = "glücklich"
                self.difficulty_level = "C2"
                self.lemma = "glücklich"
                self.concept_id = None

        filter_result = {"blocking_words": [MockWord()]}
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        word = vocabulary[0]

        # Bug #8: This assertion would FAIL with buggy code (concept_id = "glücklich-C2")
        try:
            parsed_uuid = uuid.UUID(word["concept_id"])
            assert str(parsed_uuid) == word["concept_id"], "UUID should be in canonical string format"
        except ValueError as e:
            pytest.fail(
                f"Bug #8: concept_id is not valid UUID: '{word['concept_id']}' - "
                f"causes 422 error when marking word as known. Error: {e}"
            )

    def test_uuid_deterministic(self):
        """
        Test that same word+difficulty generates same UUID (deterministic)
        This ensures users can mark words as known consistently
        """
        service = VocabularyFilterService()

        class MockWord:
            def __init__(self):
                self.word = "glücklich"
                self.difficulty_level = "C2"
                self.lemma = "glücklich"

        filter_result = {"blocking_words": [MockWord()]}

        # Generate vocabulary twice
        vocabulary1 = service.extract_vocabulary_from_result(filter_result)
        vocabulary2 = service.extract_vocabulary_from_result(filter_result)

        # Same word should generate same UUID
        assert (
            vocabulary1[0]["concept_id"] == vocabulary2[0]["concept_id"]
        ), "Same word+difficulty must generate same UUID (deterministic)"

    def test_all_vocabulary_words_have_valid_uuids(self):
        """
        Comprehensive test: ALL vocabulary words must have valid UUIDs
        This is what the previous tests were missing!
        """
        service = VocabularyFilterService()

        class MockWord:
            def __init__(self, word, difficulty, lemma=None):
                self.word = word
                self.difficulty_level = difficulty
                self.lemma = lemma
                self.concept_id = None  # Simulates real FilteredWord

        filter_result = {
            "blocking_words": [
                MockWord("glücklich", "C2", "glücklich"),
                MockWord("Haus", "A1", "haus"),
                MockWord("verstehen", "B2", "verstehen"),
            ]
        }

        vocabulary = service.extract_vocabulary_from_result(filter_result)

        # Validate EVERY word
        for word in vocabulary:
            # Bug #7: concept_id must never be None
            assert word["concept_id"] is not None, f"Bug #7: concept_id is None for word '{word['word']}'"

            # Bug #8: concept_id must be valid UUID
            try:
                uuid.UUID(word["concept_id"])
            except ValueError:
                pytest.fail(f"Bug #8: concept_id '{word['concept_id']}' is not valid UUID for word '{word['word']}'")

    def test_concept_id_without_lemma(self):
        """
        Test UUID generation when word has no lemma
        Should use word itself as identifier
        """
        service = VocabularyFilterService()

        class MockWord:
            def __init__(self):
                self.word = "test"
                self.difficulty_level = "A1"
                self.lemma = None  # No lemma

        filter_result = {"blocking_words": [MockWord()]}
        vocabulary = service.extract_vocabulary_from_result(filter_result)

        word = vocabulary[0]

        # Must still generate valid UUID even without lemma
        assert word["concept_id"] is not None
        try:
            uuid.UUID(word["concept_id"])
        except ValueError:
            pytest.fail(f"Failed to generate valid UUID without lemma: {word['concept_id']}")
