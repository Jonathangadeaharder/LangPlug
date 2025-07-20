#!/usr/bin/env python3
"""
Database Configuration for A1Decider

Centralized configuration for database settings, connection parameters,
and migration options.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class DatabaseConfig:
    """Database configuration management."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize database configuration.
        
        Args:
            base_dir: Base directory for the A1Decider project
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and defaults."""
        # Database file settings
        self.database_name = os.getenv('A1DECIDER_DB_NAME', 'a1decider.db')
        self.database_path = self.base_dir / self.database_name
        
        # Backup settings
        self.backup_dir = self.base_dir / 'backups'
        self.max_backups = int(os.getenv('A1DECIDER_MAX_BACKUPS', '10'))
        self.auto_backup = os.getenv('A1DECIDER_AUTO_BACKUP', 'true').lower() == 'true'
        
        # Performance settings
        self.connection_timeout = int(os.getenv('A1DECIDER_DB_TIMEOUT', '30'))
        self.cache_size = int(os.getenv('A1DECIDER_CACHE_SIZE', '10000'))
        self.journal_mode = os.getenv('A1DECIDER_JOURNAL_MODE', 'WAL')
        
        # Migration settings
        self.migration_batch_size = int(os.getenv('A1DECIDER_MIGRATION_BATCH_SIZE', '1000'))
        self.migration_backup = os.getenv('A1DECIDER_MIGRATION_BACKUP', 'true').lower() == 'true'
        
        # Logging settings
        self.log_level = os.getenv('A1DECIDER_LOG_LEVEL', 'INFO')
        self.log_sql_queries = os.getenv('A1DECIDER_LOG_SQL', 'false').lower() == 'true'
        
        # Data validation settings
        self.validate_words = os.getenv('A1DECIDER_VALIDATE_WORDS', 'true').lower() == 'true'
        self.min_word_length = int(os.getenv('A1DECIDER_MIN_WORD_LENGTH', '2'))
        self.max_word_length = int(os.getenv('A1DECIDER_MAX_WORD_LENGTH', '50'))
        
        # Language settings
        self.default_language = os.getenv('A1DECIDER_DEFAULT_LANGUAGE', 'de')
        self.supported_languages = os.getenv(
            'A1DECIDER_SUPPORTED_LANGUAGES', 'de,en'
        ).split(',')
    
    @property
    def connection_string(self) -> str:
        """Get the SQLite connection string."""
        return f"sqlite:///{self.database_path}"
    
    @property
    def sqlite_pragmas(self) -> Dict[str, Any]:
        """Get SQLite PRAGMA settings for optimal performance."""
        return {
            'journal_mode': self.journal_mode,
            'synchronous': 'NORMAL',
            'cache_size': self.cache_size,
            'foreign_keys': 'ON',
            'temp_store': 'MEMORY',
            'mmap_size': 268435456,  # 256MB
            'busy_timeout': self.connection_timeout * 1000  # Convert to milliseconds
        }
    
    def get_migration_config(self) -> Dict[str, Any]:
        """Get configuration for data migration."""
        return {
            'source_directory': self.base_dir,
            'backup_before_migration': self.migration_backup,
            'batch_size': self.migration_batch_size,
            'validate_data': self.validate_words,
            'default_language': self.default_language,
            'word_validation': {
                'min_length': self.min_word_length,
                'max_length': self.max_word_length
            }
        }
    
    def get_backup_config(self) -> Dict[str, Any]:
        """Get configuration for database backups."""
        return {
            'backup_directory': self.backup_dir,
            'max_backups': self.max_backups,
            'auto_backup': self.auto_backup,
            'compression': True,
            'include_timestamp': True
        }
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.backup_dir.mkdir(exist_ok=True)
        
        # Create database directory if it doesn't exist
        self.database_path.parent.mkdir(exist_ok=True)
    
    def validate_config(self) -> bool:
        """Validate the current configuration."""
        try:
            # Check if base directory exists
            if not self.base_dir.exists():
                raise ValueError(f"Base directory does not exist: {self.base_dir}")
            
            # Validate numeric settings
            if self.cache_size <= 0:
                raise ValueError("Cache size must be positive")
            
            if self.connection_timeout <= 0:
                raise ValueError("Connection timeout must be positive")
            
            if self.max_backups < 0:
                raise ValueError("Max backups cannot be negative")
            
            # Validate language settings
            if not self.default_language:
                raise ValueError("Default language cannot be empty")
            
            if self.default_language not in self.supported_languages:
                raise ValueError(f"Default language '{self.default_language}' not in supported languages")
            
            # Validate word length settings
            if self.min_word_length <= 0:
                raise ValueError("Minimum word length must be positive")
            
            if self.max_word_length <= self.min_word_length:
                raise ValueError("Maximum word length must be greater than minimum")
            
            return True
            
        except ValueError as e:
            print(f"Configuration validation error: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'database': {
                'name': self.database_name,
                'path': str(self.database_path),
                'connection_string': self.connection_string
            },
            'performance': {
                'cache_size': self.cache_size,
                'connection_timeout': self.connection_timeout,
                'journal_mode': self.journal_mode,
                'pragmas': self.sqlite_pragmas
            },
            'backup': self.get_backup_config(),
            'migration': self.get_migration_config(),
            'validation': {
                'validate_words': self.validate_words,
                'min_word_length': self.min_word_length,
                'max_word_length': self.max_word_length
            },
            'language': {
                'default': self.default_language,
                'supported': self.supported_languages
            },
            'logging': {
                'level': self.log_level,
                'log_sql_queries': self.log_sql_queries
            }
        }
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"DatabaseConfig(db_path={self.database_path}, language={self.default_language})"


# Global configuration instance
_config_instance = None


def get_database_config(base_dir: Optional[str] = None) -> DatabaseConfig:
    """Get the global database configuration instance."""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = DatabaseConfig(base_dir)
        _config_instance.ensure_directories()
        
        if not _config_instance.validate_config():
            raise RuntimeError("Invalid database configuration")
    
    return _config_instance


def reset_config():
    """Reset the global configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None


# Configuration constants for backward compatibility
DEFAULT_DATABASE_NAME = 'a1decider.db'
DEFAULT_LANGUAGE = 'de'
SUPPORTED_LANGUAGES = ['de', 'en']
DEFAULT_CACHE_SIZE = 10000
DEFAULT_TIMEOUT = 30


# File paths for migration (relative to base directory)
MIGRATION_SOURCE_FILES = {
    'unknown_words': 'globalunknowns.json',
    'vocabulary_files': [
        'vocabulary.txt',
        'giuliwords.txt',
        'charaktere.txt'
    ],
    'config_file': 'config.py'
}


# Database schema version
SCHEMA_VERSION = '1.0.0'


# Default word categories
DEFAULT_CATEGORIES = [
    ('Nouns', 'Substantive - naming words for people, places, things'),
    ('Verbs', 'Verben - action and state words'),
    ('Adjectives', 'Adjektive - descriptive words'),
    ('Adverbs', 'Adverbien - words that modify verbs, adjectives, or other adverbs'),
    ('Prepositions', 'Präpositionen - words that show relationships between other words'),
    ('Conjunctions', 'Konjunktionen - connecting words'),
    ('Articles', 'Artikel - definite and indefinite articles'),
    ('Pronouns', 'Pronomen - words that replace nouns'),
    ('Numbers', 'Zahlen - cardinal and ordinal numbers'),
    ('Common Words', 'Häufige Wörter - most frequently used words'),
    ('Academic', 'Akademische Wörter - academic and formal vocabulary'),
    ('Everyday', 'Alltägliche Wörter - everyday conversation vocabulary'),
    ('Technical', 'Technische Begriffe - technical and specialized terms'),
    ('Idioms', 'Redewendungen - idiomatic expressions'),
    ('Slang', 'Umgangssprache - informal and colloquial expressions')
]


if __name__ == '__main__':
    # Test configuration
    config = get_database_config()
    print("Database Configuration:")
    print(f"Database path: {config.database_path}")
    print(f"Default language: {config.default_language}")
    print(f"Cache size: {config.cache_size}")
    print(f"Backup directory: {config.backup_dir}")
    print(f"Configuration valid: {config.validate_config()}")