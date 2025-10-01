#!/usr/bin/env python3
"""Check glücklich entries in vocabulary database"""

from sqlalchemy import create_engine, text

# Try both database files
for db_file in ["./data/langplug.db", "./data/vocabulary.db"]:
    try:
        engine = create_engine(f"sqlite:///{db_file}")

        with engine.connect() as conn:
            # First check if table exists
            tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in tables_result]

            if "vocabulary_words" not in tables:
                continue

            result = conn.execute(
                text("""
                SELECT word, lemma, difficulty_level, part_of_speech
                FROM vocabulary_words
                WHERE word LIKE '%glücklich%' OR lemma LIKE '%glücklich%'
                ORDER BY word
                LIMIT 20
            """)
            )

            rows = list(result)
            if not rows:
                pass
            else:
                for _row in rows:
                    pass
            break

    except Exception:
        continue
