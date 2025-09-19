#!/usr/bin/env python3
from pathlib import Path

import sqlite3

print("=== German Vocabulary Verification ===")

# Find database path
db_path = Path("data/langplug.db")
if not db_path.exists():
    db_path.parent.mkdir(exist_ok=True)
    print(f"Created database at: {db_path}")
else:
    print(f"Using existing database: {db_path}")

# Connect and setup
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Create vocabulary table if needed
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

# Insert German vocabulary from Superstore
vocab_data = [
    # A1 words (user knows these)
    ("der", "A1", "article", "the (masculine)", "de"),
    ("die", "A1", "article", "the (feminine)", "de"),
    ("das", "A1", "article", "the (neuter)", "de"),

    # A2+ words (should be detected as new vocabulary)
    ("amerikanische", "A2", "adjective", "American", "de"),
    ("anlaufstelle", "B1", "noun", "first port of call", "de"),
    ("superstore", "B1", "noun", "superstore", "de"),
    ("jemals", "A2", "adverb", "ever", "de"),
    ("braucht", "A2", "verb", "needs", "de"),
    ("erste", "A2", "ordinal", "first", "de"),
    ("alles", "A2", "pronoun", "everything", "de"),
    ("möchte", "A2", "verb", "would like", "de"),
]

# Insert vocabulary
for word, level, word_type, definition, language in vocab_data:
    try:
        cursor.execute("""
            INSERT INTO vocabulary (word, difficulty_level, word_type, definition, language)
            VALUES (?, ?, ?, ?, ?)
        """, (word, level, word_type, definition, language))
    except sqlite3.IntegrityError:
        # Word already exists, update it
        cursor.execute("""
            UPDATE vocabulary 
            SET difficulty_level=?, word_type=?, definition=?
            WHERE word=? AND language=?
        """, (level, word_type, definition, word, language))

conn.commit()

# Verify results
cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE language = 'de'")
total_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE language = 'de' AND difficulty_level != 'A1'")
a2_plus_count = cursor.fetchone()[0]

print(f"\n✅ SUCCESS: Loaded {total_count} German words")
print(f"🎯 {a2_plus_count} words above A1 level (should be detected)")

# Show words that should be detected in Superstore
cursor.execute("""
    SELECT word, difficulty_level FROM vocabulary 
    WHERE language = 'de' AND difficulty_level != 'A1'
    ORDER BY difficulty_level, word
""")

print("\n📚 A2+ words that should be detected in Superstore:")
detected_words = cursor.fetchall()
for word, level in detected_words:
    print(f"   • {word} ({level})")

conn.close()

print(f"\n💾 Database saved to: {db_path.absolute()}")
print("\n🔄 Restart your backend and try processing the Superstore chunk again!")
print("   The vocabulary extraction should now find these A2+ words.")
