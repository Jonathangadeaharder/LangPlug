"""
Simple import script for German-Spanish vocabulary pairs
"""

import asyncio
import csv
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, init_db
from database.models import Language, VocabularyConcept, VocabularyTranslation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_languages(session: AsyncSession) -> None:
    """Setup supported languages in the database"""
    languages = [
        ("de", "German", "Deutsch"),
        ("es", "Spanish", "Español"),
    ]

    for code, name, native_name in languages:
        # Check if language already exists
        result = await session.execute(select(Language).where(Language.code == code))
        existing = result.scalar_one_or_none()

        if not existing:
            language = Language(code=code, name=name, native_name=native_name, is_active=True)
            session.add(language)
            logger.info(f"Added language: {name} ({code})")

    await session.commit()


def read_csv_pairs(filename: str) -> list[tuple[str, str, str]]:
    """Read German-Spanish pairs from CSV file"""
    pairs = []
    level = filename.split("_")[0]  # Extract level from filename like "A1_vokabeln.csv"

    try:
        with open(filename, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    german = row[0].strip()
                    spanish = row[1].strip()
                    pairs.append((german, spanish, level.upper()))
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")

    return pairs


async def import_vocabulary_pairs(pairs: list[tuple[str, str, str]], session: AsyncSession) -> int:
    """Import vocabulary pairs into the database one by one"""
    imported_count = 0
    skipped_count = 0

    for german, spanish, level in pairs:
        try:
            # Start a new transaction for each pair
            async with session.begin():
                # Check if a concept with this German word already exists
                result = await session.execute(
                    select(VocabularyTranslation).where(
                        VocabularyTranslation.word == german, VocabularyTranslation.language_code == "de"
                    )
                )
                existing_translation = result.scalar_one_or_none()

                if existing_translation:
                    # Concept already exists, check if Spanish translation exists
                    concept_id = existing_translation.concept_id

                    # Check for existing Spanish translation
                    spanish_result = await session.execute(
                        select(VocabularyTranslation).where(
                            VocabularyTranslation.concept_id == concept_id, VocabularyTranslation.language_code == "es"
                        )
                    )
                    existing_spanish = spanish_result.scalar_one_or_none()

                    if existing_spanish:
                        logger.debug(f"Skipping existing pair: {german} -> {spanish}")
                        skipped_count += 1
                        continue
                    else:
                        # Add Spanish translation to existing concept
                        spanish_translation = VocabularyTranslation(
                            id=str(uuid.uuid4()), concept_id=concept_id, language_code="es", word=spanish, lemma=spanish
                        )
                        session.add(spanish_translation)
                        imported_count += 1
                        logger.debug(f"Added Spanish translation for existing concept: {german} -> {spanish}")
                else:
                    # Create new concept and both translations
                    concept = VocabularyConcept(
                        id=str(uuid.uuid4()), difficulty_level=level, semantic_category="unknown", domain="general"
                    )
                    session.add(concept)

                    # Add German translation
                    german_translation = VocabularyTranslation(
                        id=str(uuid.uuid4()), concept_id=concept.id, language_code="de", word=german, lemma=german
                    )
                    session.add(german_translation)

                    # Add Spanish translation
                    spanish_translation = VocabularyTranslation(
                        id=str(uuid.uuid4()), concept_id=concept.id, language_code="es", word=spanish, lemma=spanish
                    )
                    session.add(spanish_translation)

                    imported_count += 1
                    logger.debug(f"Created new concept: {german} ({level}) -> {spanish}")

                # Commit the transaction (automatically done by async with session.begin())

        except Exception as e:
            logger.error(f"Error importing pair {german} -> {spanish}: {e}")
            # Transaction is automatically rolled back due to exception
            continue

    logger.info(f"Successfully imported {imported_count} vocabulary pairs, skipped {skipped_count} existing pairs")
    return imported_count


async def main():
    """Main import function"""
    logger.info("Starting multilingual vocabulary import...")

    # Initialize database
    await init_db()

    async with AsyncSessionLocal() as session:
        # Setup languages
        await setup_languages(session)

        # CSV files to process (just A1 for testing)
        csv_files = ["A1_vokabeln.csv"]

        total_imported = 0

        for csv_file in csv_files:
            csv_path = Path(csv_file)
            if csv_path.exists():
                logger.info(f"Processing {csv_file}...")
                pairs = read_csv_pairs(csv_file)
                logger.info(f"Found {len(pairs)} vocabulary pairs in {csv_file}")

                if pairs:
                    # Take only first 10 pairs for testing
                    test_pairs = pairs[:10]
                    imported = await import_vocabulary_pairs(test_pairs, session)
                    total_imported += imported
                    logger.info(f"Imported {imported} pairs from {csv_file} (testing with {len(test_pairs)} pairs)")
                else:
                    logger.warning(f"No valid pairs found in {csv_file}")
            else:
                logger.warning(f"File not found: {csv_file}")

        logger.info(f"Import completed. Total concepts imported: {total_imported}")

        # Print summary statistics
        from sqlalchemy import func as sql_func

        concept_count_result = await session.execute(select(sql_func.count(VocabularyConcept.id)))
        concept_count = concept_count_result.scalar()

        translation_count_result = await session.execute(select(sql_func.count(VocabularyTranslation.id)))
        translation_count = translation_count_result.scalar()

        logger.info(f"Database now contains {concept_count} concepts and {translation_count} translations")


if __name__ == "__main__":
    asyncio.run(main())
