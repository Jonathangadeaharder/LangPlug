import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('ENVIRONMENT', 'development')

import asyncio

from sqlalchemy import text

from core.database import get_async_session, init_database

# German vocabulary data
vocab_data = [
    # A1 Level
    ("der", "A1", "article", "the (masculine)", "de"),
    ("die", "A1", "article", "the (feminine)", "de"),
    ("das", "A1", "article", "the (neuter)", "de"),
    ("und", "A1", "conjunction", "and", "de"),
    ("ist", "A1", "verb", "is", "de"),
    ("haben", "A1", "verb", "to have", "de"),
    ("sein", "A1", "verb", "to be", "de"),
    ("gehen", "A1", "verb", "to go", "de"),
    ("gut", "A1", "adjective", "good", "de"),
    ("groß", "A1", "adjective", "big", "de"),

    # A2 Level - Words from Superstore subtitles
    ("können", "A2", "verb", "can/to be able to", "de"),
    ("werden", "A2", "verb", "to become/will", "de"),
    ("möchten", "A2", "verb", "would like to", "de"),
    ("braucht", "A2", "verb", "needs", "de"),
    ("jemals", "A2", "adverb", "ever", "de"),
    ("erste", "A2", "ordinal", "first", "de"),
    ("alles", "A2", "pronoun", "everything", "de"),
    ("amerikanische", "A2", "adjective", "American", "de"),

    # B1 Level - More complex Superstore words
    ("Anlaufstelle", "B1", "noun", "point of contact/first port of call", "de"),
    ("glücklicher", "B1", "adjective", "happier", "de"),
    ("schlanker", "B1", "adjective", "slimmer", "de"),
    ("fetter", "B1", "adjective", "fatter", "de"),
    ("Superstore", "B1", "noun", "superstore", "de"),

    # B2 Level
    ("Eigenschaft", "B2", "noun", "characteristic/property", "de"),
    ("Bewusstsein", "B2", "noun", "consciousness", "de"),
]

async def quick_load_vocab_async():
    print("Quick loading German vocabulary...")

    # Initialize database
    await init_database()

    async with get_async_session() as session:
        # Clear existing German vocab
        await session.execute(text("DELETE FROM vocabulary WHERE language = 'de'"))

        # Insert vocabulary
        for word, level, word_type, definition, language in vocab_data:
            await session.execute(text("""
                INSERT OR REPLACE INTO vocabulary (word, difficulty_level, word_type, definition, language)
                VALUES (:word, :level, :word_type, :definition, :language)
            """), {
                "word": word,
                "level": level,
                "word_type": word_type,
                "definition": definition,
                "language": language
            })

        await session.commit()

        # Verify
        result = await session.execute(text("SELECT COUNT(*) FROM vocabulary WHERE language = 'de'"))
        count = result.scalar()
        print(f"Loaded {count} German words")

        # Show A2+ words
        result = await session.execute(text("SELECT word, difficulty_level FROM vocabulary WHERE language = 'de' AND difficulty_level != 'A1'"))
        print("A2+ words in database:")
        for row in result.fetchall():
            print(f"  {row[0]} - {row[1]}")

    print("✅ German vocabulary loaded successfully!")

if __name__ == "__main__":
    asyncio.run(quick_load_vocab_async())
