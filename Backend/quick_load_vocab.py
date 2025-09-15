import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('ENVIRONMENT', 'development')

from database.unified_database_manager import UnifiedDatabaseManager as DatabaseManager
from core.config import settings

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

print("Quick loading German vocabulary...")
db_path = settings.get_database_path()
db = DatabaseManager(db_path)

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # Create table
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
    
    # Clear existing German vocab
    cursor.execute("DELETE FROM vocabulary WHERE language = 'de'")
    
    # Insert vocabulary
    for word, level, word_type, definition, language in vocab_data:
        cursor.execute("""
            INSERT OR REPLACE INTO vocabulary (word, difficulty_level, word_type, definition, language)
            VALUES (?, ?, ?, ?, ?)
        """, (word, level, word_type, definition, language))
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE language = 'de'")
    count = cursor.fetchone()[0]
    print(f"Loaded {count} German words")
    
    # Show A2+ words
    cursor.execute("SELECT word, difficulty_level FROM vocabulary WHERE language = 'de' AND difficulty_level != 'A1'")
    print("A2+ words in database:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - {row[1]}")

print("✅ German vocabulary loaded successfully!")
