#!/usr/bin/env python3
"""
Initialize vocabulary database with preloaded data
"""

import sys

try:
    from database.database_manager import DatabaseManager
    from services.vocabulary_preload_service import VocabularyPreloadService
    
    print("Initializing vocabulary database...")
    
    # Initialize database (this automatically creates it if it doesn't exist)
    db_manager = DatabaseManager(enable_logging=True)
    print("Database initialized successfully")
    
    # Load vocabulary
    preload_service = VocabularyPreloadService(db_manager)
    result = preload_service.load_vocabulary_files()
    print(f"Vocabulary loaded: {result}")
    
    total_loaded = sum(result.values())
    print(f"Total words loaded: {total_loaded}")
    
    # Get stats
    stats = preload_service.get_vocabulary_stats()
    print(f"Database stats: {stats}")
    
    print("Vocabulary initialization completed successfully!")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)