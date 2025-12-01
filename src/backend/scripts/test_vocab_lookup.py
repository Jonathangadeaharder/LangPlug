#!/usr/bin/env python
"""Diagnose vocabulary lookup issues"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.database import AsyncSessionLocal
from services.vocabulary.vocabulary_service import VocabularyService


async def main():
    print("[INFO] Testing German vocabulary lookups...\n")

    vocab_service = VocabularyService()

    # Test common German words
    test_words = [
        "ist",  # is (very common)
        "und",  # and (very common)
        "haben",  # to have (common verb)
        "gehen",  # to go (common verb)
        "schwierig",  # difficult (B1-B2)
    ]

    async with AsyncSessionLocal() as db:
        print(f"[INFO] Testing {len(test_words)} German words:")
        print("=" * 70)

        for word in test_words:
            try:
                result = await vocab_service.get_word_info(word, "de", db)

                if result:
                    difficulty = result.get("difficulty_level", "NOT_FOUND")
                    lemma = result.get("lemma", "NOT_FOUND")
                    print(f"\n[FOUND] '{word}':")
                    print(f"  Lemma: {lemma}")
                    print(f"  Difficulty: {difficulty}")
                    print(f"  Full result: {result}")
                else:
                    print(f"\n[NOT FOUND] '{word}' -> result is None/empty")

            except Exception as e:
                print(f"\n[ERROR] '{word}' -> {e}")

        print("\n" + "=" * 70)
        print("\n[INFO] Checking vocabulary_words table...")

        # Count German words in database
        from sqlalchemy import text

        result = await db.execute(text("SELECT COUNT(*) FROM vocabulary_words WHERE language = 'de'"))
        de_count = result.scalar()

        result = await db.execute(text("SELECT COUNT(*) FROM vocabulary_words"))
        total_count = result.scalar()

        print(f"  German words in DB: {de_count}")
        print(f"  Total words in DB: {total_count}")

        if de_count == 0:
            print("\n[WARNING] No German words found in vocabulary_words table!")
            print("[WARNING] All words will default to C2 level!")


if __name__ == "__main__":
    asyncio.run(main())
