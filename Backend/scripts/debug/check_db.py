#!/usr/bin/env python3
from pathlib import Path

import sqlite3

# Check both databases
db_files = [
    Path("data/langplug.db"),
    Path("data/vocabulary.db"),
    Path("vocabulary.db")
]

for db_path in db_files:
    if db_path.exists():
        print(f"\n=== {db_path} ===")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")

        # Check vocabulary table schema if it exists
        if any('vocabulary' in str(t) for t in tables):
            cursor.execute("PRAGMA table_info(vocabulary)")
            schema = cursor.fetchall()
            print("Vocabulary table schema:")
            for row in schema:
                print(f"  {row[1]} {row[2]} (nullable: {not row[3]}) (default: {row[4]})")

        conn.close()
    else:
        print(f"{db_path} does not exist")
