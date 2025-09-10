#!/usr/bin/env python3
"""
Unified database migration system for LangPlug
Consolidates all migration scripts into a single system
"""

import sqlite3
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class Migration:
    """Base class for database migrations"""
    
    def __init__(self, version: int, name: str):
        self.version = version
        self.name = name
        self.applied_at = None
    
    def up(self, conn: sqlite3.Connection):
        """Apply the migration"""
        raise NotImplementedError
    
    def down(self, conn: sqlite3.Connection):
        """Rollback the migration"""
        raise NotImplementedError


class MigrationRunner:
    """Manages and runs database migrations"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.migrations: List[Migration] = []
        
    def add_migration(self, migration: Migration):
        """Add a migration to the runner"""
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def ensure_migrations_table(self, conn: sqlite3.Connection):
        """Create migrations tracking table if it doesn't exist"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    def get_applied_migrations(self, conn: sqlite3.Connection) -> List[int]:
        """Get list of applied migration versions"""
        cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
        return [row[0] for row in cursor.fetchall()]
    
    def apply_migration(self, conn: sqlite3.Connection, migration: Migration):
        """Apply a single migration"""
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        try:
            migration.up(conn)
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (migration.version, migration.name)
            )
            conn.commit()
            logger.info(f"Migration {migration.version} applied successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise
    
    def run(self):
        """Run all pending migrations"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            self.ensure_migrations_table(conn)
            applied = self.get_applied_migrations(conn)
            
            pending = [m for m in self.migrations if m.version not in applied]
            
            if not pending:
                logger.info("No pending migrations")
                return
            
            logger.info(f"Found {len(pending)} pending migrations")
            
            for migration in pending:
                self.apply_migration(conn, migration)
            
            logger.info("All migrations completed successfully")
            
        finally:
            conn.close()


# Define all migrations
class InitialSchemaMigration(Migration):
    """Initial database schema"""
    
    def __init__(self):
        super().__init__(1, "initial_schema")
    
    def up(self, conn: sqlite3.Connection):
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Vocabulary table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                category TEXT,
                difficulty_level TEXT,
                frequency INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User progress table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                is_known BOOLEAN DEFAULT 0,
                confidence_level INTEGER DEFAULT 0,
                last_seen TIMESTAMP,
                times_seen INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (word_id) REFERENCES vocabulary(id),
                UNIQUE(user_id, word_id)
            )
        """)
    
    def down(self, conn: sqlite3.Connection):
        conn.execute("DROP TABLE IF EXISTS user_progress")
        conn.execute("DROP TABLE IF EXISTS vocabulary")
        conn.execute("DROP TABLE IF EXISTS users")


class AddLanguagePreferencesMigration(Migration):
    """Add language preferences to users table"""
    
    def __init__(self):
        super().__init__(2, "add_language_preferences")
    
    def up(self, conn: sqlite3.Connection):
        # Check if columns already exist
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'preferred_language' not in columns:
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN preferred_language TEXT DEFAULT 'de'
            """)
        
        if 'subtitle_language' not in columns:
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN subtitle_language TEXT DEFAULT 'en'
            """)
    
    def down(self, conn: sqlite3.Connection):
        # SQLite doesn't support dropping columns directly
        # Would need to recreate table without these columns
        pass


class AddVocabularyIndexesMigration(Migration):
    """Add indexes for better query performance"""
    
    def __init__(self):
        super().__init__(3, "add_vocabulary_indexes")
    
    def up(self, conn: sqlite3.Connection):
        # Check if columns exist before creating indexes
        cursor = conn.execute("PRAGMA table_info(vocabulary)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Create indexes only for existing columns
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vocabulary_word ON vocabulary(word)")
        
        if 'category' in columns:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vocabulary_category ON vocabulary(category)")
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_progress(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_progress_word ON user_progress(word_id)")
    
    def down(self, conn: sqlite3.Connection):
        conn.execute("DROP INDEX IF EXISTS idx_vocabulary_word")
        conn.execute("DROP INDEX IF EXISTS idx_vocabulary_category")
        conn.execute("DROP INDEX IF EXISTS idx_user_progress_user")
        conn.execute("DROP INDEX IF EXISTS idx_user_progress_word")


class AddSessionTableMigration(Migration):
    """Add session management table"""
    
    def __init__(self):
        super().__init__(4, "add_session_table")
    
    def up(self, conn: sqlite3.Connection):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")
    
    def down(self, conn: sqlite3.Connection):
        conn.execute("DROP TABLE IF EXISTS sessions")


def run_migrations(db_path: Path):
    """Run all database migrations"""
    runner = MigrationRunner(db_path)
    
    # Add all migrations
    runner.add_migration(InitialSchemaMigration())
    runner.add_migration(AddLanguagePreferencesMigration())
    runner.add_migration(AddVocabularyIndexesMigration())
    runner.add_migration(AddSessionTableMigration())
    
    # Run migrations
    runner.run()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get database path from settings
    from core.config import settings
    db_path = settings.get_database_path()
    
    logger.info(f"Running migrations for database: {db_path}")
    run_migrations(db_path)