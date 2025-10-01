"""
Test the multilingual vocabulary system
"""

import asyncio
import logging

from sqlalchemy import func as sql_func
from sqlalchemy import select

from core.database import AsyncSessionLocal
from database.models import Language, VocabularyConcept, VocabularyTranslation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_multilingual_system():
    """Test the multilingual vocabulary system"""
    logger.info("Testing multilingual vocabulary system...")

    async with AsyncSessionLocal() as session:
        # Test 1: Count concepts and translations
        concept_count_result = await session.execute(select(sql_func.count(VocabularyConcept.id)))
        concept_count = concept_count_result.scalar()

        translation_count_result = await session.execute(select(sql_func.count(VocabularyTranslation.id)))
        translation_count = translation_count_result.scalar()

        logger.info(f"Database contains {concept_count} concepts and {translation_count} translations")

        # Test 2: Get sample German-Spanish pairs
        pairs_result = await session.execute(
            select(VocabularyTranslation.word.label("german"), VocabularyTranslation.language_code.label("german_lang"))
            .where(VocabularyTranslation.language_code == "de")
            .limit(5)
        )
        german_words = pairs_result.fetchall()

        logger.info("Sample German words:")
        for word in german_words:
            # Find Spanish translation for this concept
            german_trans_result = await session.execute(
                select(VocabularyTranslation.concept_id).where(
                    VocabularyTranslation.word == word.german, VocabularyTranslation.language_code == "de"
                )
            )
            concept_id = german_trans_result.scalar_one_or_none()

            if concept_id:
                spanish_result = await session.execute(
                    select(VocabularyTranslation.word).where(
                        VocabularyTranslation.concept_id == concept_id, VocabularyTranslation.language_code == "es"
                    )
                )
                spanish_word = spanish_result.scalar_one_or_none()
                logger.info(f"  {word.german} -> {spanish_word or 'NO TRANSLATION'}")

        # Test 3: Get concepts by level
        for level in ["A1"]:
            level_result = await session.execute(
                select(sql_func.count(VocabularyConcept.id)).where(VocabularyConcept.difficulty_level == level)
            )
            level_count = level_result.scalar()
            logger.info(f"Level {level}: {level_count} concepts")

        # Test 4: Check languages
        lang_result = await session.execute(select(Language))
        languages = lang_result.scalars().all()
        logger.info(f"Supported languages: {[(lang.code, lang.name) for lang in languages]}")

        logger.info("✅ Multilingual system test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_multilingual_system())
