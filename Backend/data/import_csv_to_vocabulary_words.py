#!/usr/bin/env python3
"""
Import German-Spanish vocabulary from CSV files into vocabulary_words table.
Populates the correct table that the application uses for lookups.
"""

import asyncio
import csv
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, init_db
from database.models import VocabularyWord

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def read_csv_vocabulary(filename: str, level: str) -> list[tuple[str, str, str]]:
    """
    Read vocabulary pairs from CSV file.

    Args:
        filename: Path to CSV file
        level: CEFR level (A1, A2, B1, B2, C1, C2)

    Returns:
        List of (german_word, spanish_translation, level) tuples
    """
    pairs = []

    try:
        with open(filename, encoding="utf-8") as f:
            reader = csv.reader(f)
            for _row_num, row in enumerate(reader, 1):
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    german = row[0].strip()
                    spanish = row[1].strip()
                    pairs.append((german, spanish, level))

        logger.info(f"Read {len(pairs)} vocabulary pairs from {filename}")

    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")

    return pairs


async def import_to_vocabulary_words(
    pairs: list[tuple[str, str, str]], session: AsyncSession, language: str = "de"
) -> int:
    """
    Import vocabulary pairs into vocabulary_words table.

    Args:
        pairs: List of (german_word, spanish_translation, level) tuples
        session: Database session
        language: Language code for German words

    Returns:
        Number of words imported
    """
    imported_count = 0
    skipped_count = 0
    updated_count = 0

    for german, spanish, level in pairs:
        try:
            # Check if word already exists
            result = await session.execute(
                select(VocabularyWord).where(VocabularyWord.word == german, VocabularyWord.language == language)
            )
            existing_word = result.scalar_one_or_none()

            if existing_word:
                # Update Spanish translation if different
                if existing_word.translation_native != spanish:
                    existing_word.translation_native = spanish
                    existing_word.difficulty_level = level  # Update level too
                    updated_count += 1
                    logger.debug(f"Updated: {german} -> {spanish} ({level})")
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped existing: {german}")
            else:
                # Create new vocabulary word
                vocab_word = VocabularyWord(
                    word=german,
                    lemma=german.lower(),  # Simple lemmatization for now
                    language=language,
                    difficulty_level=level,
                    translation_native=spanish,  # Spanish translation
                    part_of_speech=None,  # Will be filled by NLP later
                    gender=None,  # Will be filled by NLP later
                )
                session.add(vocab_word)
                imported_count += 1
                logger.debug(f"Imported: {german} -> {spanish} ({level})")

        except Exception as e:
            logger.error(f"Error importing {german} -> {spanish}: {e}")
            continue

    # Commit all changes
    try:
        await session.commit()
        logger.info(f"Import completed: {imported_count} new, {updated_count} updated, {skipped_count} skipped")
    except Exception as e:
        logger.error(f"Failed to commit changes: {e}")
        await session.rollback()
        raise

    return imported_count


async def main():
    """Main import function."""
    logger.info("Starting vocabulary import into vocabulary_words table...")

    # Initialize database
    await init_db()

    # CSV files to import
    csv_files = {
        "A1_vokabeln.csv": "A1",
        "A2_vokabeln.csv": "A2",
        "B1_vokabeln.csv": "B1",
        "B2_vokabeln.csv": "B2",
        "C1_vokabeln.csv": "C1",
    }

    total_imported = 0

    async with AsyncSessionLocal() as session:
        for csv_file, level in csv_files.items():
            csv_path = Path(csv_file)

            if csv_path.exists():
                logger.info(f"Processing {csv_file} ({level} level)...")
                pairs = read_csv_vocabulary(csv_file, level)

                if pairs:
                    imported = await import_to_vocabulary_words(pairs, session, language="de")
                    total_imported += imported
                else:
                    logger.warning(f"No vocabulary pairs found in {csv_file}")
            else:
                logger.warning(f"File not found: {csv_file}")

        # Print final statistics
        from sqlalchemy import func

        count_result = await session.execute(
            select(func.count(VocabularyWord.id)).where(VocabularyWord.language == "de")
        )
        total_words = count_result.scalar()

        logger.info(f"Import completed. Total German words in database: {total_words}")

        # Verify glücklich is there
        result = await session.execute(
            select(VocabularyWord).where(VocabularyWord.word == "glücklich", VocabularyWord.language == "de")
        )
        gluecklich = result.scalar_one_or_none()

        if gluecklich:
            logger.info(f"✓ Verified: glücklich ({gluecklich.difficulty_level}) -> {gluecklich.translation_native}")
        else:
            logger.warning("✗ glücklich not found in database after import!")


if __name__ == "__main__":
    asyncio.run(main())
