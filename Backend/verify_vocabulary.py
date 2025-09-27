#!/usr/bin/env python3
"""
Verify vocabulary import and show statistics
"""

import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from database.models import VocabularyConcept, VocabularyTranslation
from core.database import get_async_session

async def main():
    print("[INFO] Vocabulary Database Status")
    print("=" * 50)

    async for session in get_async_session():
        try:
            # Count total concepts
            concept_count = await session.execute(
                select(func.count(VocabularyConcept.id))
            )
            total_concepts = concept_count.scalar()

            # Count German words
            german_count = await session.execute(
                select(func.count(VocabularyTranslation.id)).where(
                    VocabularyTranslation.language_code == 'de'
                )
            )
            total_german = german_count.scalar()

            # Count Spanish words
            spanish_count = await session.execute(
                select(func.count(VocabularyTranslation.id)).where(
                    VocabularyTranslation.language_code == 'es'
                )
            )
            total_spanish = spanish_count.scalar()

            print(f"\n[GOOD] Database Statistics:")
            print(f"  Total concepts: {total_concepts}")
            print(f"  German words: {total_german}")
            print(f"  Spanish words: {total_spanish}")

            # Show distribution by level
            print("\n[INFO] Distribution by difficulty level:")
            for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                level_count = await session.execute(
                    select(func.count(VocabularyConcept.id)).where(
                        VocabularyConcept.difficulty_level == level
                    )
                )
                count = level_count.scalar()

                if level == "C2":
                    print(f"  {level}: {count} concepts (reserved for new discoveries)")
                else:
                    print(f"  {level}: {count} concepts")

            # Sample some words to verify
            print("\n[INFO] Sample vocabulary (first 5 A1 words):")
            sample_concepts = await session.execute(
                select(VocabularyConcept)
                .where(VocabularyConcept.difficulty_level == 'A1')
                .limit(5)
            )

            for concept in sample_concepts.scalars():
                # Get translations for this concept
                translations = await session.execute(
                    select(VocabularyTranslation).where(
                        VocabularyTranslation.concept_id == concept.id
                    )
                )

                words = {}
                for trans in translations.scalars():
                    words[trans.language_code] = trans.word

                if 'de' in words and 'es' in words:
                    print(f"  {words['de']} -> {words['es']} (Level: {concept.difficulty_level})")

            print("\n[GOOD] Vocabulary system is ready!")
            print("[INFO] Configuration:")
            print("  - A1-C1 vocabulary loaded from CSV files")
            print("  - New words from videos will be classified as C2")
            print("  - System configured for German to Spanish learning")

            break

        except Exception as e:
            print(f"[ERROR] Failed to verify vocabulary: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    asyncio.run(main())