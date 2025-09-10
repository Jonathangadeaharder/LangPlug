#!/usr/bin/env python3
"""
Direct test of database operations to isolate the hang
"""

import sys
sys.path.append('Backend')

from database.database_manager import DatabaseManager
import time

def test_database_operations():
    """Test basic database operations directly"""
    
    print("Testing direct database operations...")
    print("=" * 50)
    
    try:
        # Create database manager
        print("1. Creating DatabaseManager...")
        start_time = time.time()
        
        # Use simple path for testing
        db_path = "Backend/vocabulary.db"
        print(f"   Database path: {db_path}")
        
        db_manager = DatabaseManager(db_path)
        elapsed = time.time() - start_time
        print(f"   [OK] DatabaseManager created in {elapsed:.3f} seconds")
        
        # Test simple query
        print("2. Testing simple query...")
        start_time = time.time()
        
        result = db_manager.execute_query("SELECT 1 as test")
        elapsed = time.time() - start_time
        print(f"   [OK] Simple query completed in {elapsed:.3f} seconds: {result}")
        
        # Test user table query (this is where it hangs)
        print("3. Testing user table query...")
        start_time = time.time()
        
        results = db_manager.execute_query("""
            SELECT id, username, password_hash, salt, is_admin, is_active, created_at, updated_at, last_login
            FROM users WHERE username = ?
        """, ("admin",))
        
        elapsed = time.time() - start_time
        print(f"   [OK] User query completed in {elapsed:.3f} seconds")
        print(f"   Results found: {len(results)}")
        if results:
            print(f"   First result: {dict(results[0])}")
        
        print("\n" + "=" * 50)
        print("SUCCESS: All database operations working!")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   [ERROR] Database operation failed after {elapsed:.3f} seconds: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_operations()