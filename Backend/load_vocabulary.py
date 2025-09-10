"""Load complete vocabulary database with all difficulty levels"""
import sqlite3
from pathlib import Path

def load_vocabulary_database():
    """Load all vocabulary words from text files into database"""
    
    # Database path
    db_path = Path("data/vocabulary.db")
    db_path.parent.mkdir(exist_ok=True)
    
    print(f"Database path: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check current count
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    current_count = cursor.fetchone()[0]
    print(f"Current vocabulary count: {current_count}")
    
    if current_count > 0:
        print(f"Database already contains {current_count} words")
        response = input("Do you want to reload all vocabulary? (y/n): ")
        if response.lower() != 'y':
            print("Keeping existing vocabulary")
            return
        else:
            print("Clearing existing vocabulary...")
            cursor.execute("DELETE FROM vocabulary")
            conn.commit()
    
    # Load vocabulary files
    vocab_files = {
        'A1': Path("../archived/vocabulary_a1.txt"),
        'A2': Path("../archived/vocabulary_a2.txt"), 
        'B1': Path("../archived/vocabulary_b1.txt"),
        'B2': Path("../archived/vocabulary_b2.txt")
    }
    
    # Try alternative locations if files not found
    alt_vocab_files = {
        'A1': Path("vocabulary_a1.txt"),
        'A2': Path("vocabulary_a2.txt"),
        'B1': Path("vocabulary_b1.txt"),
        'B2': Path("vocabulary_b2.txt")
    }
    
    total_loaded = 0
    
    for level, file_path in vocab_files.items():
        if not file_path.exists():
            # Try alternative location
            alt_path = alt_vocab_files[level]
            if alt_path.exists():
                file_path = alt_path
            else:
                print(f"Warning: {level} vocabulary file not found at {file_path} or {alt_path}")
                # Create sample vocabulary for this level
                sample_words = generate_sample_vocabulary(level)
                print(f"Generated {len(sample_words)} sample {level} words")
                
                for word in sample_words:
                    cursor.execute("""
                        INSERT INTO vocabulary (word, difficulty_level, created_at, updated_at)
                        VALUES (?, ?, datetime('now'), datetime('now'))
                    """, (word, level))
                
                total_loaded += len(sample_words)
                continue
        
        print(f"\nLoading {level} vocabulary from {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            
            print(f"Found {len(words)} {level} words")
            
            # Insert words into database
            for word in words:
                cursor.execute("""
                    INSERT INTO vocabulary (word, difficulty_level, created_at, updated_at)
                    VALUES (?, ?, datetime('now'), datetime('now'))
                """, (word, level))
            
            total_loaded += len(words)
            print(f"Loaded {len(words)} {level} words")
            
        except Exception as e:
            print(f"Error loading {level} vocabulary: {e}")
    
    # Commit all changes
    conn.commit()
    
    # Verify final count
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    final_count = cursor.fetchone()[0]
    
    # Get count by level
    cursor.execute("""
        SELECT difficulty_level, COUNT(*) 
        FROM vocabulary 
        GROUP BY difficulty_level
        ORDER BY difficulty_level
    """)
    level_counts = cursor.fetchall()
    
    print(f"\n{'='*50}")
    print("Vocabulary Loading Complete!")
    print(f"{'='*50}")
    print(f"Total words loaded: {total_loaded}")
    print(f"Total words in database: {final_count}")
    print("\nWords by difficulty level:")
    for level, count in level_counts:
        print(f"  {level}: {count} words")
    
    conn.close()
    print(f"\nDatabase saved to: {db_path.absolute()}")

def generate_sample_vocabulary(level):
    """Generate sample vocabulary for a given level"""
    sample_words = {
        'A1': [
            # Basic greetings and common words
            'hallo', 'guten Tag', 'auf Wiedersehen', 'danke', 'bitte',
            'ja', 'nein', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr',
            'der', 'die', 'das', 'ein', 'eine', 'und', 'oder', 'aber',
            'haben', 'sein', 'werden', 'können', 'müssen', 'wollen',
            'machen', 'gehen', 'kommen', 'sehen', 'geben', 'nehmen',
            'gut', 'schlecht', 'groß', 'klein', 'alt', 'neu', 'jung',
            'heute', 'morgen', 'gestern', 'jetzt', 'später', 'immer',
            'eins', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben',
            'acht', 'neun', 'zehn', 'hundert', 'tausend',
            'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag',
            'Samstag', 'Sonntag', 'Januar', 'Februar', 'März', 'April',
            'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober',
            'November', 'Dezember', 'Frühling', 'Sommer', 'Herbst', 'Winter',
            'Haus', 'Auto', 'Buch', 'Tisch', 'Stuhl', 'Fenster', 'Tür',
            'Mann', 'Frau', 'Kind', 'Mutter', 'Vater', 'Bruder', 'Schwester',
            'Freund', 'Freundin', 'Familie', 'Schule', 'Arbeit', 'Zeit'
        ],
        'A2': [
            # Intermediate basic vocabulary
            'verstehen', 'sprechen', 'lesen', 'schreiben', 'hören',
            'arbeiten', 'lernen', 'studieren', 'wohnen', 'leben',
            'kaufen', 'verkaufen', 'bezahlen', 'kosten', 'brauchen',
            'mögen', 'lieben', 'hassen', 'denken', 'glauben',
            'Restaurant', 'Café', 'Supermarkt', 'Bahnhof', 'Flughafen',
            'Krankenhaus', 'Apotheke', 'Post', 'Bank', 'Hotel'
        ],
        'B1': [
            # Lower intermediate vocabulary
            'Meinung', 'Entscheidung', 'Erfahrung', 'Möglichkeit', 'Problem',
            'entwickeln', 'verbessern', 'erklären', 'beschreiben', 'vergleichen',
            'Umwelt', 'Gesundheit', 'Bildung', 'Politik', 'Wirtschaft'
        ],
        'B2': [
            # Upper intermediate vocabulary
            'Zusammenhang', 'Voraussetzung', 'Konsequenz', 'Perspektive', 'Analyse',
            'interpretieren', 'argumentieren', 'kritisieren', 'evaluieren', 'reflektieren'
        ]
    }
    
    return sample_words.get(level, [])

if __name__ == "__main__":
    load_vocabulary_database()