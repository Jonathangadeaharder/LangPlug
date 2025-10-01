#!/usr/bin/env python3
"""
Standalone import script for vocabulary CSV files.
Directly imports into vocabulary_words table without app dependencies.
"""

import asyncio
import csv
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database URL (using the langplug.db that the app uses)
DATABASE_URL = "sqlite+aiosqlite:///./langplug.db"


def read_csv_vocabulary(filename: str, level: str) -> list[tuple[str, str, str]]:
    """Read vocabulary pairs from CSV file."""
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


async def import_vocabulary(pairs: list[tuple[str, str, str]], async_session: async_sessionmaker) -> int:
    """Import vocabulary pairs into database."""
    imported_count = 0
    skipped_count = 0
    updated_count = 0

    async with async_session() as session:
        for german, spanish, level in pairs:
            try:
                # Check if word exists
                existing = await session.execute(
                    text("""
                        SELECT id, translation_native
                        FROM vocabulary_words
                        WHERE word = :word AND language = :lang
                    """),
                    {"word": german, "lang": "de"},
                )
                existing_row = existing.fetchone()

                if existing_row:
                    word_id, current_translation = existing_row

                    if current_translation != spanish:
                        # Update translation
                        await session.execute(
                            text("""
                                UPDATE vocabulary_words
                                SET translation_native = :spanish,
                                    difficulty_level = :level,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = :id
                            """),
                            {"spanish": spanish, "level": level, "id": word_id},
                        )
                        updated_count += 1
                        logger.debug(f"Updated: {german} -> {spanish} ({level})")
                    else:
                        skipped_count += 1
                else:
                    # Insert new word
                    await session.execute(
                        text("""
                            INSERT INTO vocabulary_words
                            (word, lemma, language, difficulty_level, translation_native, created_at, updated_at)
                            VALUES (:word, :lemma, :lang, :level, :spanish, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """),
                        {"word": german, "lemma": german.lower(), "lang": "de", "level": level, "spanish": spanish},
                    )
                    imported_count += 1
                    logger.debug(f"Imported: {german} -> {spanish} ({level})")

            except Exception as e:
                logger.error(f"Error importing {german}: {e}")
                continue

        # Commit all changes
        try:
            await session.commit()
            logger.info(f"Import completed: {imported_count} new, {updated_count} updated, {skipped_count} skipped")
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            await session.rollback()
            raise

    return imported_count


async def main():
    """Main import function."""
    logger.info("Starting vocabulary import...")

    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # CSV files to import
    csv_files = {
        "A1_vokabeln.csv": "A1",
        "A2_vokabeln.csv": "A2",
        "B1_vokabeln.csv": "B1",
        "B2_vokabeln.csv": "B2",
        "C1_vokabeln.csv": "C1",
    }

    total_imported = 0

    for csv_file, level in csv_files.items():
        csv_path = Path(csv_file)

        if csv_path.exists():
            logger.info(f"Processing {csv_file} ({level} level)...")
            pairs = read_csv_vocabulary(csv_file, level)

            if pairs:
                imported = await import_vocabulary(pairs, async_session)
                total_imported += imported
            else:
                logger.warning(f"No vocabulary pairs found in {csv_file}")
        else:
            logger.warning(f"File not found: {csv_file}")

    # Verify import
    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM vocabulary_words WHERE language = 'de'"))
        total_words = result.scalar()
        logger.info(f"Total German words in database: {total_words}")

        # Check for glücklich
        result = await session.execute(
            text("""
                SELECT word, difficulty_level, translation_native
                FROM vocabulary_words
                WHERE word = 'glücklich' AND language = 'de'
            """)
        )
        gluecklich_row = result.fetchone()

        if gluecklich_row:
            word, level, translation = gluecklich_row
            logger.info(f"✓ Verified: {word} ({level}) -> {translation}")
        else:
            logger.warning("✗ glücklich not found after import!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
