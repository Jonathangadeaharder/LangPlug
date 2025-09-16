#!/usr/bin/env python3
"""
Load German vocabulary data into the database
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault('ENVIRONMENT', 'development')

async def load_german_vocabulary_async():
    """Load German vocabulary data into database"""
    print("Loading German Vocabulary Data")
    print("=============================\n")
    
    try:
        from core.database import get_async_session, init_database
        from core.config import settings
        import asyncio
        from sqlalchemy import text
        
        # Sample German vocabulary with CEFR levels
        german_vocabulary = [
            # A1 Level - Basic words
            ("der", "A1", "article", "the (masculine)"),
            ("die", "A1", "article", "the (feminine)"),
            ("das", "A1", "article", "the (neuter)"),
            ("und", "A1", "conjunction", "and"),
            ("ich", "A1", "pronoun", "I"),
            ("du", "A1", "pronoun", "you (informal)"),
            ("er", "A1", "pronoun", "he"),
            ("sie", "A1", "pronoun", "she/they"),
            ("es", "A1", "pronoun", "it"),
            ("ist", "A1", "verb", "is"),
            ("bin", "A1", "verb", "am"),
            ("haben", "A1", "verb", "to have"),
            ("sein", "A1", "verb", "to be"),
            ("machen", "A1", "verb", "to make/do"),
            ("gehen", "A1", "verb", "to go"),
            ("kommen", "A1", "verb", "to come"),
            ("sehen", "A1", "verb", "to see"),
            ("wollen", "A1", "verb", "to want"),
            ("gut", "A1", "adjective", "good"),
            ("groß", "A1", "adjective", "big"),
            ("klein", "A1", "adjective", "small"),
            ("neu", "A1", "adjective", "new"),
            ("alt", "A1", "adjective", "old"),
            ("schön", "A1", "adjective", "beautiful"),
            ("Haus", "A1", "noun", "house"),
            ("Auto", "A1", "noun", "car"),
            ("Mann", "A1", "noun", "man"),
            ("Frau", "A1", "noun", "woman"),
            ("Kind", "A1", "noun", "child"),
            ("Tag", "A1", "noun", "day"),
            ("Jahr", "A1", "noun", "year"),
            ("Zeit", "A1", "noun", "time"),
            ("Wasser", "A1", "noun", "water"),
            ("Brot", "A1", "noun", "bread"),
            
            # A2 Level - Common words
            ("können", "A2", "verb", "can/to be able to"),
            ("müssen", "A2", "verb", "must/to have to"),
            ("sollen", "A2", "verb", "should/ought to"),
            ("werden", "A2", "verb", "to become/will"),
            ("möchten", "A2", "verb", "would like to"),
            ("arbeiten", "A2", "verb", "to work"),
            ("lernen", "A2", "verb", "to learn"),
            ("kaufen", "A2", "verb", "to buy"),
            ("sprechen", "A2", "verb", "to speak"),
            ("verstehen", "A2", "verb", "to understand"),
            ("wichtig", "A2", "adjective", "important"),
            ("interessant", "A2", "adjective", "interesting"),
            ("schwierig", "A2", "adjective", "difficult"),
            ("einfach", "A2", "adjective", "simple"),
            ("richtig", "A2", "adjective", "correct"),
            ("falsch", "A2", "adjective", "wrong"),
            ("Arbeit", "A2", "noun", "work"),
            ("Schule", "A2", "noun", "school"),
            ("Familie", "A2", "noun", "family"),
            ("Freund", "A2", "noun", "friend"),
            ("Problem", "A2", "noun", "problem"),
            ("Welt", "A2", "noun", "world"),
            ("Stadt", "A2", "noun", "city"),
            ("Land", "A2", "noun", "country"),
            ("Geld", "A2", "noun", "money"),
            ("jemals", "A2", "adverb", "ever"),
            ("braucht", "A2", "verb", "needs"),
            ("erste", "A2", "ordinal", "first"),
            ("alles", "A2", "pronoun", "everything"),
            
            # B1 Level - Intermediate words  
            ("Anlaufstelle", "B1", "noun", "point of contact/first port of call"),
            ("glücklicher", "B1", "adjective", "happier"),
            ("schlanker", "B1", "adjective", "slimmer"),
            ("fetter", "B1", "adjective", "fatter"),
            ("entwickeln", "B1", "verb", "to develop"),
            ("entscheiden", "B1", "verb", "to decide"),
            ("erklären", "B1", "verb", "to explain"),
            ("bedeuten", "B1", "verb", "to mean"),
            ("erreichen", "B1", "verb", "to reach"),
            ("verwenden", "B1", "verb", "to use"),
            ("behandeln", "B1", "verb", "to treat"),
            ("bestimmt", "B1", "adjective", "certain/specific"),
            ("besonders", "B1", "adverb", "especially"),
            ("plötzlich", "B1", "adverb", "suddenly"),
            ("möglich", "B1", "adjective", "possible"),
            ("notwendig", "B1", "adjective", "necessary"),
            ("Möglichkeit", "B1", "noun", "possibility"),
            ("Erfahrung", "B1", "noun", "experience"),
            ("Entwicklung", "B1", "noun", "development"),
            ("Gesellschaft", "B1", "noun", "society"),
            ("Beziehung", "B1", "noun", "relationship"),
            ("Situation", "B1", "noun", "situation"),
            ("Entscheidung", "B1", "noun", "decision"),
            ("Verantwortung", "B1", "noun", "responsibility"),
            
            # B2 Level - Advanced words
            ("Eigenschaft", "B2", "noun", "characteristic/property"),
            ("Bewusstsein", "B2", "noun", "consciousness"),
            ("Auseinandersetzung", "B2", "noun", "confrontation/discussion"),
            ("Veränderung", "B2", "noun", "change"),
            ("Herausforderung", "B2", "noun", "challenge"),
            ("Unternehmen", "B2", "noun", "company/enterprise"),
            ("Voraussetzung", "B2", "noun", "prerequisite"),
            ("berücksichtigen", "B2", "verb", "to consider/take into account"),
            ("beurteilen", "B2", "verb", "to judge/assess"),
            ("bezeichnen", "B2", "verb", "to designate/describe"),
            ("beeinflussen", "B2", "verb", "to influence"),
            ("entsprechen", "B2", "verb", "to correspond"),
            ("vergleichen", "B2", "verb", "to compare"),
            ("wesentlich", "B2", "adjective", "essential"),
            ("erheblich", "B2", "adjective", "considerable"),
            ("ausschließlich", "B2", "adverb", "exclusively"),
            ("grundsätzlich", "B2", "adverb", "fundamentally"),
            ("beziehungsweise", "B2", "conjunction", "respectively/or rather"),
        ]
        
        # Initialize database
        await init_database()
        print("Database initialized")
        
        async with get_async_session() as session:
            # Create vocabulary table if it doesn't exist (handled by models)
            
            # Clear existing German vocabulary
            await session.execute(text("DELETE FROM vocabulary WHERE language = :lang"), {"lang": "de"})
            print("Cleared existing German vocabulary")
            
            # Insert German vocabulary
            inserted = 0
            for word, level, word_type, definition in german_vocabulary:
                try:
                    await session.execute(text("""
                        INSERT INTO vocabulary (word, difficulty_level, word_type, definition, language)
                        VALUES (:word, :level, :word_type, :definition, :language)
                    """), {
                        "word": word,
                        "level": level, 
                        "word_type": word_type,
                        "definition": definition,
                        "language": "de"
                    })
                    inserted += 1
                except Exception as e:
                    print(f"Failed to insert '{word}': {e}")
            
            await session.commit()
            print(f"✅ Inserted {inserted} German vocabulary words")
            
            # Verify insertion
            result = await session.execute(text("SELECT COUNT(*) FROM vocabulary WHERE language = :lang"), {"lang": "de"})
            total_german = result.scalar()
            print(f"Total German words in database: {total_german}")
            
            # Show breakdown by level
            for level in ["A1", "A2", "B1", "B2"]:
                result = await session.execute(text("SELECT COUNT(*) FROM vocabulary WHERE language = :lang AND difficulty_level = :level"), {"lang": "de", "level": level})
                count = result.scalar()
                print(f"  {level}: {count} words")
        
        print("\n✅ German vocabulary loaded successfully!")
        print("Now the difficulty filter should identify words above A1 level.")
        
    except Exception as e:
        print(f"❌ Error loading German vocabulary: {e}")
        import traceback
        traceback.print_exc()

def load_german_vocabulary():
    """Sync wrapper for loading German vocabulary"""
    asyncio.run(load_german_vocabulary_async())

if __name__ == "__main__":
    load_german_vocabulary()
