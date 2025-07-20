# A1Decider Database Module

This module provides a comprehensive SQLite-based database system for managing vocabulary and user data in the A1Decider project. It replaces the previous flat-file storage system with a robust, scalable, and concurrent-safe database solution.

## Features

- **SQLite Database**: Lightweight, serverless database with ACID compliance
- **Repository Pattern**: Clean separation of data access logic
- **Migration Tools**: Automated migration from flat files to database
- **Transaction Management**: Safe concurrent access with proper transaction handling
- **Comprehensive Testing**: Full test suite with unit and integration tests
- **CLI Tools**: Command-line interface for database management
- **Backup & Recovery**: Built-in backup and restore functionality
- **Performance Optimization**: Indexes, views, and query optimization

## Architecture

### Core Components

1. **DatabaseManager** (`database_manager.py`)
   - Central database connection and transaction management
   - Schema creation and validation
   - Backup and maintenance operations

2. **Repositories** (`repositories/`)
   - `VocabularyRepository`: Manage vocabulary words and their properties
   - `UnknownWordsRepository`: Track unknown words and frequencies
   - `WordCategoryRepository`: Organize words into categories
   - `UserProgressRepository`: Track learning progress and sessions

3. **Migration System** (`migration.py`)
   - Automated data migration from flat files
   - Backup creation before migration
   - Error handling and rollback capabilities

4. **Configuration** (`config.py`)
   - Centralized database settings
   - Environment variable support
   - Performance tuning parameters

## Database Schema

The database consists of the following main tables:

- **vocabulary**: Core vocabulary words with frequency and difficulty
- **unknown_words**: Words that need to be learned with frequency tracking
- **word_categories**: Hierarchical categorization system
- **word_category_associations**: Many-to-many relationships between words and categories
- **user_learning_progress**: Individual word learning progress
- **processing_sessions**: Session tracking for analytics
- **session_word_discoveries**: Words discovered in each session

## Quick Start

### 1. Installation

The database module is part of the A1Decider project. No additional installation is required beyond the project dependencies.

### 2. Create Database

```bash
# Using CLI
python database/cli.py create

# Or programmatically
from database import DatabaseManager

db_manager = DatabaseManager('vocabulary.db')
db_manager.create_database()
```

### 3. Migrate Existing Data

```bash
# Migrate from current directory
python database/cli.py migrate --source-dir . --backup

# Or programmatically
from database.migration import DataMigration

migration = DataMigration('vocabulary.db', 'source_directory')
results = migration.run_migration(backup_existing=True)
```

### 4. Basic Usage

```python
from database import DatabaseManager, VocabularyRepository, UnknownWordsRepository

# Initialize
db_manager = DatabaseManager('vocabulary.db')
vocab_repo = VocabularyRepository(db_manager)
unknown_repo = UnknownWordsRepository(db_manager)

# Add vocabulary word
word_id = vocab_repo.add_word(
    word='haus',
    frequency=10,
    difficulty_level='beginner',
    language='de'
)

# Add unknown word
unknown_repo.add_unknown_word('unbekannt', frequency=5)

# Search words
results = vocab_repo.search_words('haus', language='de')

# Get statistics
stats = vocab_repo.get_vocabulary_statistics()
```

## CLI Usage

The database module includes a comprehensive CLI tool:

```bash
# Show help
python database/cli.py --help

# Create new database
python database/cli.py create

# Migrate data with backup
python database/cli.py migrate --source-dir /path/to/files --backup

# Show database statistics
python database/cli.py stats

# Search for words
python database/cli.py search "haus"

# Create backup
python database/cli.py backup

# Vacuum database
python database/cli.py vacuum
```

## Configuration

Database configuration can be customized through environment variables or the config file:

```python
# Environment variables
A1DECIDER_DB_PATH=/path/to/database.db
A1DECIDER_DEFAULT_LANGUAGE=de
A1DECIDER_CACHE_SIZE=10000
A1DECIDER_LOG_LEVEL=INFO

# Or programmatically
from database.config import DatabaseConfig

config = DatabaseConfig('/custom/path')
config.cache_size = 20000
config.journal_mode = 'WAL'
```

## Migration from Flat Files

The migration system automatically handles the following file types:

- **globalunknowns.json**: Unknown words with frequencies
- **vocabulary.txt**: Vocabulary words with frequencies
- **giuliwords.txt**: Additional vocabulary words
- **charaktere.txt**: Character-based vocabulary

### Migration Process

1. **Backup**: Creates backup of existing database (optional)
2. **Parse Files**: Reads and validates flat file data
3. **Transform**: Converts data to database format
4. **Load**: Inserts data using batch operations
5. **Verify**: Validates migration results
6. **Report**: Generates migration summary

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python database/test_database.py

# Run specific test class
python -m unittest database.test_database.TestVocabularyRepository

# Run with verbose output
python database/test_database.py -v
```

The test suite includes:
- Unit tests for all repository classes
- Integration tests for complete workflows
- Migration testing with sample data
- Configuration validation tests
- Database manager functionality tests

## Performance Considerations

### Indexes

The database includes optimized indexes for:
- Word lookups by text
- Frequency-based queries
- Language filtering
- Category associations
- Session tracking

### Query Optimization

- Use prepared statements for repeated queries
- Batch operations for bulk inserts/updates
- Connection pooling for concurrent access
- WAL mode for better concurrent read performance

### Memory Usage

- Configurable cache size (default: 10MB)
- Lazy loading of large result sets
- Efficient pagination for large queries

## Backup and Recovery

### Automatic Backups

```python
# Create backup before migration
migration.run_migration(backup_existing=True)

# Manual backup
db_manager = DatabaseManager('vocabulary.db')
backup_path = db_manager.backup_database()
```

### Recovery

```python
# Restore from backup
import shutil
shutil.copy('backup.db', 'vocabulary.db')
```

## Troubleshooting

### Common Issues

1. **Database Locked**
   - Ensure all connections are properly closed
   - Check for long-running transactions
   - Use WAL mode for better concurrency

2. **Migration Errors**
   - Verify source file formats
   - Check file permissions
   - Review migration logs

3. **Performance Issues**
   - Increase cache size
   - Run VACUUM to optimize database
   - Check query execution plans

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with A1Decider

To integrate the database system with the main A1Decider application:

1. **Update Configuration**
   ```python
   # In config.py
   USE_DATABASE = True
   DATABASE_PATH = 'vocabulary.db'
   ```

2. **Replace File I/O**
   ```python
   # Replace flat file operations
   from database import VocabularyRepository, UnknownWordsRepository
   
   # Instead of load_word_list()
   vocab_repo = VocabularyRepository(db_manager)
   words = vocab_repo.get_all_words(language='de')
   ```

3. **Update Processing Pipeline**
   ```python
   # Track processing sessions
   progress_repo = UserProgressRepository(db_manager)
   session_id = progress_repo.create_processing_session(
       session_type='subtitle_processing',
       source_file='movie.srt'
   )
   ```

## Future Enhancements

- **Multi-user Support**: User-specific vocabulary and progress
- **Synchronization**: Cloud sync for vocabulary data
- **Analytics**: Advanced learning analytics and insights
- **Export/Import**: Various format support (CSV, JSON, XML)
- **API Integration**: RESTful API for external access
- **Machine Learning**: Intelligent word difficulty prediction

## Contributing

When contributing to the database module:

1. **Add Tests**: Include unit tests for new functionality
2. **Update Schema**: Document schema changes in `schema.sql`
3. **Migration Scripts**: Provide migration scripts for schema updates
4. **Performance**: Consider performance impact of changes
5. **Documentation**: Update this README and code documentation

## License

This module is part of the A1Decider project and follows the same license terms.