"""
Quiz Generation Service

Generates diverse quiz questions for vocabulary practice with spaced repetition.
Based on research from Vocabulary Builder project.

Question Types:
- Multiple choice (definition)
- Fill-in-the-blank
- Synonym/Antonym
- Audio pronunciation (future)
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum

from services.learning.spaced_repetition import SM2Algorithm, VocabularyReviewItem

logger = logging.getLogger(__name__)


class QuizType(str, Enum):
    """Types of quiz questions"""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SYNONYM = "synonym"
    ANTONYM = "antonym"


@dataclass
class QuizQuestion:
    """
    A single quiz question.

    Attributes:
        question_id: Unique identifier
        question_type: Type of question
        word: The vocabulary word being tested
        correct_answer: The correct answer
        options: Answer options (for multiple choice)
        hint: Optional hint for the user
        context_sentence: Optional sentence using the word
    """
    question_id: str
    question_type: QuizType
    word: str
    correct_answer: str
    options: list[str]  # For multiple choice
    hint: str | None = None
    context_sentence: str | None = None

    def check_answer(self, user_answer: str) -> bool:
        """
        Check if user's answer is correct.

        Args:
            user_answer: User's submitted answer

        Returns:
            True if correct, False otherwise
        """
        return user_answer.strip().lower() == self.correct_answer.strip().lower()


@dataclass
class QuizSession:
    """
    A complete quiz session.

    Attributes:
        session_id: Unique session identifier
        user_id: User taking the quiz
        questions: List of quiz questions
        started_at: Session start time
        completed_at: Session completion time
        score: Number of correct answers
        total_questions: Total number of questions
    """
    session_id: str
    user_id: int
    questions: list[QuizQuestion]
    started_at: str
    completed_at: str | None = None
    score: int = 0
    total_questions: int = 0

    def __post_init__(self):
        self.total_questions = len(self.questions)


class QuizGenerator:
    """
    Generate diverse quiz questions for vocabulary practice.

    Uses spaced repetition algorithm to select due words and creates
    varied question types to test different aspects of vocabulary knowledge.

    Example:
        ```python
        generator = QuizGenerator(db_session)

        # Generate quiz session
        session = await generator.generate_quiz_session(
            user_id=123,
            num_questions=10,
            quiz_types=[QuizType.MULTIPLE_CHOICE, QuizType.FILL_BLANK]
        )

        # Present questions to user
        for question in session.questions:
            print(f"Q: {question.word}")
            if question.question_type == QuizType.MULTIPLE_CHOICE:
                for i, option in enumerate(question.options, 1):
                    print(f"  {i}. {option}")
        ```
    """

    def __init__(self, db_session):
        """
        Initialize quiz generator.

        Args:
            db_session: Database session for fetching vocabulary
        """
        self.db = db_session
        self.sm2 = SM2Algorithm()

    async def generate_quiz_session(
        self,
        user_id: int,
        num_questions: int = 10,
        quiz_types: list[QuizType] | None = None,
        difficulty_filter: str | None = None
    ) -> QuizSession:
        """
        Generate a complete quiz session with mixed question types.

        Selection strategy:
        1. Prioritize due vocabulary items (using SM-2 algorithm)
        2. Include difficult words (low easiness factor)
        3. Mix in recently encountered words
        4. Randomize question types

        Args:
            user_id: User ID
            num_questions: Number of questions (default: 10)
            quiz_types: Question types to include (default: all)
            difficulty_filter: Optional CEFR level filter (A1, A2, etc.)

        Returns:
            QuizSession with generated questions

        Example:
            >>> session = await generator.generate_quiz_session(
            ...     user_id=123,
            ...     num_questions=15,
            ...     quiz_types=[QuizType.MULTIPLE_CHOICE, QuizType.FILL_BLANK],
            ...     difficulty_filter="A2"
            ... )
            >>> print(f"Quiz ready: {session.total_questions} questions")
        """
        import uuid
        from datetime import datetime

        # Default to all question types
        if quiz_types is None:
            quiz_types = [QuizType.MULTIPLE_CHOICE, QuizType.FILL_BLANK]

        # Get user's vocabulary items
        user_vocab = await self._get_user_vocabulary(
            user_id,
            difficulty_filter=difficulty_filter
        )

        # Convert to VocabularyReviewItem format
        review_items = [
            self._to_review_item(vocab)
            for vocab in user_vocab
        ]

        # Get due items using spaced repetition
        due_items = self.sm2.get_due_items(review_items)

        # If not enough due items, add random items
        if len(due_items) < num_questions:
            non_due = [item for item in review_items if item not in due_items]
            random.shuffle(non_due)
            due_items.extend(non_due[:num_questions - len(due_items)])

        # Select items for quiz
        quiz_items = due_items[:num_questions]

        # Generate questions with mixed types
        questions = []
        for i, item in enumerate(quiz_items):
            # Randomly select question type
            quiz_type = random.choice(quiz_types)

            question_id = f"q_{uuid.uuid4().hex[:8]}"

            if quiz_type == QuizType.MULTIPLE_CHOICE:
                question = await self.generate_multiple_choice(
                    question_id,
                    item.word,
                    item.translation,
                    user_id
                )
            elif quiz_type == QuizType.FILL_BLANK:
                question = self.generate_fill_blank(
                    question_id,
                    item.word,
                    item.translation
                )
            elif quiz_type == QuizType.SYNONYM:
                question = await self.generate_synonym_question(
                    question_id,
                    item.word,
                    item.translation,
                    user_id
                )
            else:
                # Fallback to multiple choice
                question = await self.generate_multiple_choice(
                    question_id,
                    item.word,
                    item.translation,
                    user_id
                )

            questions.append(question)

        # Create quiz session
        session = QuizSession(
            session_id=f"quiz_{user_id}_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            questions=questions,
            started_at=datetime.now().isoformat()
        )

        logger.info(f"Generated quiz session {session.session_id} with {len(questions)} questions")

        return session

    async def generate_multiple_choice(
        self,
        question_id: str,
        word: str,
        correct_translation: str,
        user_id: int,
        num_options: int = 4
    ) -> QuizQuestion:
        """
        Generate multiple choice question with distractors.

        Distractor selection strategy:
        - Similar difficulty level (CEFR)
        - Same word class (noun, verb, etc.) if possible
        - Different enough to avoid confusion

        Args:
            question_id: Unique question identifier
            word: The vocabulary word
            correct_translation: Correct answer
            user_id: User ID (for personalized distractors)
            num_options: Number of answer options (default: 4)

        Returns:
            QuizQuestion with multiple choice format

        Example:
            >>> question = await generator.generate_multiple_choice(
            ...     "q1", "Hund", "dog", user_id=123
            ... )
            >>> print(question.options)
            ['dog', 'cat', 'bird', 'fish']  # Random order
        """
        # Get similar words as distractors
        distractors = await self._get_similar_words(
            word,
            num_options - 1,
            user_id
        )

        # Build options list
        options = [correct_translation] + [d['translation'] for d in distractors]

        # Shuffle options
        random.shuffle(options)

        return QuizQuestion(
            question_id=question_id,
            question_type=QuizType.MULTIPLE_CHOICE,
            word=word,
            correct_answer=correct_translation,
            options=options,
            hint=f"What is the English translation of '{word}'?"
        )

    def generate_fill_blank(
        self,
        question_id: str,
        word: str,
        correct_translation: str,
        sentence_context: str | None = None
    ) -> QuizQuestion:
        """
        Generate fill-in-the-blank question.

        Uses sentence context if provided, otherwise creates simple prompt.

        Args:
            question_id: Unique question identifier
            word: The vocabulary word
            correct_translation: Correct answer
            sentence_context: Optional sentence using the word

        Returns:
            QuizQuestion with fill-in-the-blank format

        Example:
            >>> question = generator.generate_fill_blank(
            ...     "q2", "Hund", "dog",
            ...     sentence_context="Der Hund ist groß"
            ... )
            >>> print(question.context_sentence)
            'Der ______ ist groß'
        """
        if sentence_context:
            # Replace word with blank
            blank_sentence = sentence_context.replace(word, "______")
            hint = "Complete the sentence"
        else:
            blank_sentence = f"'{word}' means ______"
            hint = "Type the English translation"

        return QuizQuestion(
            question_id=question_id,
            question_type=QuizType.FILL_BLANK,
            word=word,
            correct_answer=correct_translation,
            options=[],  # Free text input
            hint=hint,
            context_sentence=blank_sentence
        )

    async def generate_synonym_question(
        self,
        question_id: str,
        word: str,
        correct_translation: str,
        user_id: int
    ) -> QuizQuestion:
        """
        Generate synonym identification question.

        Args:
            question_id: Unique question identifier
            word: The vocabulary word
            correct_translation: Correct answer
            user_id: User ID

        Returns:
            QuizQuestion asking to identify synonym

        Example:
            >>> question = await generator.generate_synonym_question(
            ...     "q3", "groß", "big", user_id=123
            ... )
            >>> print(question.hint)
            'Which word is a synonym for "groß"?'
        """
        # Get related words
        related = await self._get_related_words(word, 3, user_id)

        options = [correct_translation] + [r['translation'] for r in related]
        random.shuffle(options)

        return QuizQuestion(
            question_id=question_id,
            question_type=QuizType.SYNONYM,
            word=word,
            correct_answer=correct_translation,
            options=options,
            hint=f'Which word is most similar in meaning to "{word}"?'
        )

    async def _get_user_vocabulary(
        self,
        user_id: int,
        difficulty_filter: str | None = None
    ) -> list[dict]:
        """
        Fetch user's vocabulary from database.

        Args:
            user_id: User ID
            difficulty_filter: Optional CEFR level filter

        Returns:
            List of vocabulary dictionaries
        """
        # This would query the actual database
        # Placeholder implementation
        return []

    def _to_review_item(self, vocab_dict: dict) -> VocabularyReviewItem:
        """
        Convert database vocabulary to VocabularyReviewItem.

        Args:
            vocab_dict: Vocabulary dictionary from database

        Returns:
            VocabularyReviewItem for spaced repetition
        """
        from datetime import datetime

        return VocabularyReviewItem(
            word=vocab_dict.get('word', ''),
            translation=vocab_dict.get('translation', ''),
            easiness_factor=vocab_dict.get('easiness_factor', 2.5),
            repetitions=vocab_dict.get('repetitions', 0),
            interval=vocab_dict.get('interval_days', 1),
            next_review=datetime.fromisoformat(vocab_dict['next_review'])
            if vocab_dict.get('next_review')
            else datetime.now(),
            last_reviewed=datetime.fromisoformat(vocab_dict['last_reviewed'])
            if vocab_dict.get('last_reviewed')
            else None,
            total_reviews=vocab_dict.get('total_reviews', 0),
            correct_reviews=vocab_dict.get('correct_reviews', 0)
        )

    async def _get_similar_words(
        self,
        word: str,
        count: int,
        user_id: int
    ) -> list[dict]:
        """
        Get similar words for distractor generation.

        Strategy:
        - Same difficulty level
        - Different lemma
        - Preferably same word class

        Args:
            word: Word to find similar words for
            count: Number of similar words needed
            user_id: User ID

        Returns:
            List of similar word dictionaries
        """
        # Placeholder - would query database for similar words
        return [
            {'translation': f'distractor_{i}'}
            for i in range(count)
        ]

    async def _get_related_words(
        self,
        word: str,
        count: int,
        user_id: int
    ) -> list[dict]:
        """
        Get related words (synonyms, related concepts).

        Args:
            word: Word to find related words for
            count: Number of related words needed
            user_id: User ID

        Returns:
            List of related word dictionaries
        """
        # Placeholder - would use word embeddings or synonym database
        return [
            {'translation': f'related_{i}'}
            for i in range(count)
        ]
