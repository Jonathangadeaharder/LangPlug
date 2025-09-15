#!/usr/bin/env python3
"""
Quick script to check vocabulary database content
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault('ENVIRONMENT', 'development')

def check_vocab_db():
    """Check vocabulary database content"""
    print("Checking Vocabulary Database")
    print("===========================\n")
    
    try:
        from database.unified_database_manager import UnifiedDatabaseManager as DatabaseManager
        from core.config import settings
        
        db_path = settings.get_database_path()
        print(f"Database path: {db_path}")
        
        if not Path(db_path).exists():
            print("❌ Database file does not exist!")
            return
        
        db = DatabaseManager(db_path)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check total vocabulary count
            cursor.execute("SELECT COUNT(*) FROM vocabulary")
            total_count = cursor.fetchone()[0]
            print(f"Total vocabulary words: {total_count}")
            
            # Check German words
            cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE language = ?", ("de",))
            german_count = cursor.fetchone()[0]
            print(f"German words: {german_count}")
            
            if german_count > 0:
                print("\nSample German words:")
                cursor.execute("SELECT word, difficulty_level FROM vocabulary WHERE language = ? LIMIT 10", ("de",))
                for row in cursor.fetchall():
                    print(f"  {row[0]} - {row[1]}")
                    
                # Check for words that might be in Superstore subtitles
                test_words = ["der", "die", "das", "und", "ist", "sein", "haben", "werden", "können", "möchten", "erste", "alles"]
                print(f"\nChecking for common German words in DB:")
                for word in test_words:
                    cursor.execute("SELECT difficulty_level FROM vocabulary WHERE word = ? AND language = ?", (word, "de"))
                    result = cursor.fetchone()
                    if result:
                        print(f"  ✅ {word} - {result[0]}")
                    else:
                        print(f"  ❌ {word} - NOT FOUND")
            else:
                print("❌ No German words found in database!")
                print("You need to load German vocabulary data.")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vocab_db()
