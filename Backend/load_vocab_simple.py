#!/usr/bin/env python3
from pathlib import Path

import sqlite3

# Database path - same as config
backend_path = Path(__file__).parent
db_path = backend_path / "data" / "langplug.db"

print(f"Loading vocabulary to: {db_path}")

# Ensure data directory exists
db_path.parent.mkdir(exist_ok=True)

# Connect to database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Create vocabulary table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        difficulty_level TEXT NOT NULL,
        word_type TEXT,
        definition TEXT,
        language TEXT DEFAULT 'de',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(word, language)
    )
""")

# Clear existing German vocabulary
cursor.execute("DELETE FROM vocabulary WHERE language = 'de'")

# German vocabulary with words from Superstore subtitles
vocab_data = [
    # A1 Level (user already knows these)
    ("der", "A1", "article", "the (masculine)", "de"),
    ("die", "A1", "article", "the (feminine)", "de"),
    ("das", "A1", "article", "the (neuter)", "de"),
    ("und", "A1", "conjunction", "and", "de"),
    ("ist", "A1", "verb", "is", "de"),
    ("haben", "A1", "verb", "to have", "de"),
    ("sein", "A1", "verb", "to be", "de"),
    ("man", "A1", "pronoun", "one/you", "de"),
    ("oder", "A1", "conjunction", "or", "de"),

    # A2 Level - These should be detected as new vocabulary
    ("können", "A2", "verb", "can/to be able to", "de"),
    ("werden", "A2", "verb", "to become/will", "de"),
    ("möchten", "A2", "verb", "would like to", "de"),
    ("braucht", "A2", "verb", "needs", "de"),
    ("jemals", "A2", "adverb", "ever", "de"),
    ("erste", "A2", "ordinal", "first", "de"),
    ("alles", "A2", "pronoun", "everything", "de"),
    ("amerikanische", "A2", "adjective", "American", "de"),

    # B1 Level - More advanced vocabulary from Superstore
    ("anlaufstelle", "B1", "noun", "point of contact/first port of call", "de"),
    ("superstore", "B1", "noun", "superstore", "de"),
]

# Insert vocabulary
for word, level, word_type, definition, language in vocab_data:
    cursor.execute("""
        INSERT OR REPLACE INTO vocabulary (word, difficulty_level, word_type, definition, language)
        VALUES (?, ?, ?, ?, ?)
    """, (word, level, word_type, definition, language))

conn.commit()

# Verify loading
cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE language = 'de'")
german_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE language = 'de' AND difficulty_level != 'A1'")
a2_plus_count = cursor.fetchone()[0]

print(f"✅ Loaded {german_count} German words ({a2_plus_count} above A1 level)")

# Show the A2+ words that should be detected
cursor.execute("""
    SELECT word, difficulty_level FROM vocabulary 
    WHERE language = 'de' AND difficulty_level != 'A1'
    ORDER BY difficulty_level, word
""")

print("\n🎯 A2+ words that should be detected in Superstore:")
for word, level in cursor.fetchall():
    print(f"  {word} ({level})")

conn.close()
print("\n✅ Vocabulary loading complete!")
print("🔄 Now restart your backend to see the vocabulary in action.")
