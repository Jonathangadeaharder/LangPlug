#!/usr/bin/env python3
"""
Database Manager for A1Decider Vocabulary System

Provides centralized database connection management, schema creation,
and transaction handling for the vocabulary learning system.
"""

import sqlite3
import logging
import hashlib
import secrets
from pathlib import Path
from typing import Any, Dict, List
from contextlib import contextmanager
from datetime import datetime


class DatabaseManager:
    """Manages database connections and operations for the vocabulary system."""
    
    def __init__(self, db_path: str = "vocabulary.db", enable_logging: bool = False):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
            enable_logging: Enable SQL query logging
        """
        self.db_path = Path(db_path)
        self.enable_logging = enable_logging
        self._setup_logging()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            self._create_database()
        
        self._verify_schema()
    
    def _setup_logging(self):
        """Setup logging for database operations."""
        self.logger = logging.getLogger(__name__)
        if self.enable_logging and not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path), 
                check_same_thread=False,  # CRITICAL FIX: Allow multi-threading
                timeout=10.0  # CRITICAL FIX: Prevent deadlocks
            )
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            conn.execute("PRAGMA journal_mode = WAL")  # CRITICAL FIX: Enable WAL mode for better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # CRITICAL FIX: Balance safety vs performance
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def transaction(self):
        """Execute operations within a transaction."""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Transaction failed: {e}")
                raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        if self.enable_logging:
            self.logger.info(f"Executing query: {query} with params: {params}")
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        if self.enable_logging:
            self.logger.info(f"Executing update: {query} with params: {params}")
        
        with self.transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last row ID."""
        if self.enable_logging:
            self.logger.info(f"Executing insert: {query} with params: {params}")
        
        with self.transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute a query with multiple parameter sets."""
        if self.enable_logging:
            self.logger.info(f"Executing batch: {query} with {len(params_list)} parameter sets")
        
        with self.transaction() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount
    
    def _create_database(self):
        """Create the database schema."""
        self.logger.info(f"Creating new database at {self.db_path}")
        
        schema_sql = self._get_schema_sql()
        
        with self.transaction() as conn:
            # Execute schema creation
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)
            
            # Insert default word categories
            self._insert_default_categories(conn)
            
            # Create default admin user
            self._create_default_admin_user(conn)
        
        self.logger.info("Database schema created successfully")
    
    def _get_schema_sql(self) -> str:
        """Get the complete database schema SQL."""
        return """
        -- Word Categories/Lists Management
        CREATE TABLE word_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            file_path VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Core vocabulary storage
        CREATE TABLE vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word VARCHAR(100) NOT NULL,
            lemma VARCHAR(100),
            language VARCHAR(10) DEFAULT 'de',
            difficulty_level VARCHAR(10),
            word_type VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(word, language)
        );
        
        -- Word category associations (many-to-many)
        CREATE TABLE word_category_associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES word_categories(id) ON DELETE CASCADE,
            UNIQUE(word_id, category_id)
        );
        
        -- Global unknown words tracking
        CREATE TABLE unknown_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word VARCHAR(100) NOT NULL,
            lemma VARCHAR(100),
            frequency_count INTEGER DEFAULT 1,
            first_encountered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_encountered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            language VARCHAR(10) DEFAULT 'de',
            UNIQUE(word, language)
        );
        
        -- User learning progress
        CREATE TABLE user_learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(50) DEFAULT 'default_user',
            word_id INTEGER NOT NULL,
            learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_level INTEGER DEFAULT 1,
            review_count INTEGER DEFAULT 0,
            last_reviewed TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
            UNIQUE(user_id, word_id)
        );
        
        -- Content processing sessions
        CREATE TABLE processing_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(100) UNIQUE NOT NULL,
            content_type VARCHAR(50),
            content_path VARCHAR(500),
            total_words INTEGER,
            unknown_words_found INTEGER,
            processing_time_seconds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Session word discoveries
        CREATE TABLE session_word_discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(100) NOT NULL,
            word VARCHAR(100) NOT NULL,
            frequency_in_session INTEGER DEFAULT 1,
            context_examples TEXT,
            FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id) ON DELETE CASCADE
        );
        
        -- Authentication and user management
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(32) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        
        -- User sessions for token-based authentication
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token VARCHAR(128) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        -- Indexes for performance
        CREATE INDEX idx_vocabulary_word ON vocabulary(word);
        CREATE INDEX idx_vocabulary_lemma ON vocabulary(lemma);
        CREATE INDEX idx_vocabulary_difficulty ON vocabulary(difficulty_level);
        CREATE INDEX idx_unknown_words_word ON unknown_words(word);
        CREATE INDEX idx_unknown_words_frequency ON unknown_words(frequency_count DESC);
        CREATE INDEX idx_user_progress_user ON user_learning_progress(user_id);
        CREATE INDEX idx_session_discoveries_session ON session_word_discoveries(session_id);
        CREATE INDEX idx_users_username ON users(username);
        CREATE INDEX idx_sessions_token ON user_sessions(session_token);
        CREATE INDEX idx_sessions_user ON user_sessions(user_id);
        """
    
    def _insert_default_categories(self, conn):
        """Insert default word categories based on existing file structure."""
        default_categories = [
            ('a1_words', 'A1 level German vocabulary', 'a1.txt'),
            ('charaktere', 'Character names from media', 'charaktere.txt'),
            ('giuliwords', 'Extended German vocabulary', 'giuliwords.txt'),
            ('brands', 'Brand names and commercial terms', 'brands.txt'),
            ('onomatopoeia', 'Sound words and expressions', 'onomatopoeia.txt'),
            ('interjections', 'Interjections and exclamations', 'interjections.txt')
        ]
        
        for name, description, file_path in default_categories:
            conn.execute(
                "INSERT INTO word_categories (name, description, file_path) VALUES (?, ?, ?)",
                (name, description, file_path)
            )
    
    def _create_default_admin_user(self, conn):
        """Create default admin user with username 'admin' and password 'admin'"""
        # Check if admin user already exists
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone():
            return  # Admin already exists
        
        # Create admin user with secure password hashing
        salt = secrets.token_hex(16)
        password_hash = self._hash_password("admin", salt)
        
        conn.execute("""
            INSERT INTO users (username, password_hash, salt, is_admin, created_at, updated_at)
            VALUES (?, ?, ?, TRUE, ?, ?)
        """, ("admin", password_hash, salt, datetime.now().isoformat(), datetime.now().isoformat()))
        
        self.logger.info("Default admin user created with username 'admin'")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using PBKDF2"""
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    
    def _verify_schema(self):
        """Verify that the database schema is up to date."""
        try:
            with self.get_connection() as conn:
                # Check if all required tables exist
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = {row[0] for row in cursor.fetchall()}
                
                required_tables = {
                    'word_categories', 'vocabulary', 'word_category_associations',
                    'unknown_words', 'user_learning_progress', 'processing_sessions',
                    'session_word_discoveries', 'users', 'user_sessions'
                }
                
                missing_tables = required_tables - tables
                if missing_tables:
                    self.logger.warning(f"Missing tables: {missing_tables}")
                    self._create_database()
                
        except Exception as e:
            self.logger.error(f"Schema verification failed: {e}")
            raise
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source:
                backup = sqlite3.connect(str(backup_path))
                source.backup(backup)
                backup.close()
            
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        try:
            with self.get_connection() as conn:
                # Table row counts
                tables = ['vocabulary', 'unknown_words', 'user_learning_progress', 
                         'processing_sessions', 'word_categories']
                
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Database file size
                stats['database_size_bytes'] = self.db_path.stat().st_size
                stats['database_path'] = str(self.db_path)
                stats['last_modified'] = datetime.fromtimestamp(
                    self.db_path.stat().st_mtime
                ).isoformat()
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def vacuum_database(self) -> bool:
        """Optimize database by running VACUUM."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            self.logger.info("Database vacuum completed")
            return True
        except Exception as e:
            self.logger.error(f"Database vacuum failed: {e}")
            return False