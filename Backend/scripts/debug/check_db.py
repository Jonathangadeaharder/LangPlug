#!/usr/bin/env python3
import sqlite3
from pathlib import Path

# Check both databases
db_files = [Path("data/langplug.db"), Path("data/vocabulary.db"), Path("vocabulary.db")]

for db_path in db_files:
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        # Check vocabulary table schema if it exists
        if any("vocabulary" in str(t) for t in tables):
            cursor.execute("PRAGMA table_info(vocabulary)")
            schema = cursor.fetchall()
            for _row in schema:
                pass

        conn.close()
    else:
        pass
