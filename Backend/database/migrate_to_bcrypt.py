#!/usr/bin/env python3
"""
Migration script to handle existing users with SHA256 passwords.
This script adds a flag to track which users need to update their passwords.
"""

import sys
from pathlib import Path

import sqlite3

# Add Backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime


def migrate_password_system():
    """Add migration flag for password hash migration"""
    db_path = Path(__file__).parent / "langplug.db"

    if not db_path.exists():
        print("Database not found. No migration needed.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if migration column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'needs_password_migration' not in columns:
            print("Adding password migration column...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN needs_password_migration BOOLEAN DEFAULT 1
            """)

            # Mark all existing users as needing migration
            cursor.execute("""
                UPDATE users 
                SET needs_password_migration = 1,
                    updated_at = ?
                WHERE password_hash IS NOT NULL AND password_hash != ''
            """, (datetime.now().isoformat(),))

            affected = cursor.rowcount
            print(f"Marked {affected} existing users for password migration")

            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Migration column already exists. No action needed.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_password_system()
