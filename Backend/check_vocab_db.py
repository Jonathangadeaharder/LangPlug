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

async def check_vocab_db_async():
    """Check vocabulary database content"""
    print("Checking Vocabulary Database")
    print("===========================\n")
    
    try:
        from core.database import get_async_session, init_database
        from core.config import settings
        import asyncio
        from sqlalchemy import text
        
        # Initialize database
        await init_database()
        print("Database initialized")
        
        async with get_async_session() as session:
            # Check total vocabulary count
            result = await session.execute(text("SELECT COUNT(*) FROM vocabulary"))
            total_count = result.scalar()
            print(f"Total vocabulary words: {total_count}")
            
            # Check German words
            result = await session.execute(text("SELECT COUNT(*) FROM vocabulary WHERE language = :lang"), {"lang": "de"})
            german_count = result.scalar()
            print(f"German words: {german_count}")
            
            if german_count > 0:
                print("\nSample German words:")
                result = await session.execute(text("SELECT word, difficulty_level FROM vocabulary WHERE language = :lang LIMIT 10"), {"lang": "de"})
                for row in result.fetchall():
                    print(f"  {row[0]} - {row[1]}")
                    
                # Check for words that might be in Superstore subtitles
                test_words = ["der", "die", "das", "und", "ist", "sein", "haben", "werden", "können", "möchten", "erste", "alles"]
                print(f"\nChecking for common German words in DB:")
                for word in test_words:
                    result = await session.execute(text("SELECT difficulty_level FROM vocabulary WHERE word = :word AND language = :lang"), {"word": word, "lang": "de"})
                    row = result.fetchone()
                    if row:
                        print(f"  ✅ {word} - {row[0]}")
                    else:
                        print(f"  ❌ {word} - NOT FOUND")
            else:
                print("❌ No German words found in database!")
                print("You need to load German vocabulary data.")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

def check_vocab_db():
    """Sync wrapper for checking vocabulary database"""
    asyncio.run(check_vocab_db_async())

if __name__ == "__main__":
    check_vocab_db()
