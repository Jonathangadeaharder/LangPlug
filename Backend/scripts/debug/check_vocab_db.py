#!/usr/bin/env python3
"""
Quick script to check vocabulary database content
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault("ENVIRONMENT", "development")


async def check_vocab_db_async():
    """Check vocabulary database content"""

    try:
        from sqlalchemy import text

        from core.database import get_async_session, init_database

        # Initialize database
        await init_database()

        async with get_async_session() as session:
            # Check total vocabulary count
            result = await session.execute(text("SELECT COUNT(*) FROM vocabulary"))
            result.scalar()

            # Check German words
            result = await session.execute(
                text("SELECT COUNT(*) FROM vocabulary WHERE language = :lang"), {"lang": "de"}
            )
            german_count = result.scalar()

            if german_count > 0:
                result = await session.execute(
                    text("SELECT word, difficulty_level FROM vocabulary WHERE language = :lang LIMIT 10"),
                    {"lang": "de"},
                )
                for row in result.fetchall():
                    pass

                # Check for words that might be in Superstore subtitles
                test_words = [
                    "der",
                    "die",
                    "das",
                    "und",
                    "ist",
                    "sein",
                    "haben",
                    "werden",
                    "können",
                    "möchten",
                    "erste",
                    "alles",
                ]
                for word in test_words:
                    result = await session.execute(
                        text("SELECT difficulty_level FROM vocabulary WHERE word = :word AND language = :lang"),
                        {"word": word, "lang": "de"},
                    )
                    row = result.fetchone()
                    if row:
                        pass
                    else:
                        pass
            else:
                pass

    except Exception:
        import traceback

        traceback.print_exc()


def check_vocab_db():
    """Sync wrapper for checking vocabulary database"""
    asyncio.run(check_vocab_db_async())


if __name__ == "__main__":
    check_vocab_db()
