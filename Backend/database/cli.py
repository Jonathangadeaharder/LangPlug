#!/usr/bin/env python3
"""
A1Decider Database CLI Tool

Command-line interface for database operations, migration, and management.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.database_manager import DatabaseManager
from database.migration import DataMigration
from database.repositories.vocabulary_repository import VocabularyRepository
from database.repositories.unknown_words_repository import UnknownWordsRepository
from database.repositories.word_category_repository import WordCategoryRepository
from database.repositories.user_progress_repository import UserProgressRepository
# Default database configuration
DEFAULT_DATABASE_PATH = "data/a1decider.db"


def create_database(args):
    """Create a new database with schema."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if os.path.exists(db_path) and not args.force:
        print(f"Database already exists at {db_path}")
        print("Use --force to recreate the database")
        return 1
    
    try:
        db_manager = DatabaseManager(db_path)
        db_manager.create_database()
        print(f"Database created successfully at {db_path}")
        
        # Show database statistics
        stats = db_manager.get_database_statistics()
        print(f"Database size: {stats['size_mb']:.2f} MB")
        print(f"Tables created: {stats['table_count']}")
        
        return 0
    except Exception as e:
        print(f"Error creating database: {e}")
        return 1


def migrate_data(args):
    """Migrate data from flat files to database."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    source_dir = args.source_dir or str(Path.cwd())
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Create the database first using 'create' command")
        return 1
    
    try:
        migration = DataMigration(db_path, source_dir)
        
        print(f"Starting migration from {source_dir} to {db_path}")
        print("This may take a few minutes...")
        
        results = migration.run_migration(
            backup_existing=args.backup,
            batch_size=args.batch_size
        )
        
        if results['success']:
            print("\nMigration completed successfully!")
            print(f"Vocabulary words migrated: {results['vocabulary_migrated']}")
            print(f"Unknown words migrated: {results['unknown_words_migrated']}")
            print(f"Categories created: {results['categories_created']}")
            
            if results.get('backup_path'):
                print(f"Backup created at: {results['backup_path']}")
            
            if results.get('errors'):
                print(f"\nWarnings/Errors: {len(results['errors'])}")
                for error in results['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(results['errors']) > 5:
                    print(f"  ... and {len(results['errors']) - 5} more")
        else:
            print("Migration failed!")
            if results.get('errors'):
                for error in results['errors']:
                    print(f"Error: {error}")
            return 1
        
        return 0
    except Exception as e:
        print(f"Error during migration: {e}")
        return 1


def show_stats(args):
    """Show database statistics."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        db_manager = DatabaseManager(db_path)
        vocab_repo = VocabularyRepository(db_manager)
        unknown_repo = UnknownWordsRepository(db_manager)
        category_repo = WordCategoryRepository(db_manager)
        progress_repo = UserProgressRepository(db_manager)
        
        print(f"Database Statistics for {db_path}")
        print("=" * 50)
        
        # Database info
        db_stats = db_manager.get_database_statistics()
        print(f"Database size: {db_stats['size_mb']:.2f} MB")
        print(f"Tables: {db_stats['table_count']}")
        print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
        print()
        
        # Vocabulary statistics
        vocab_stats = vocab_repo.get_vocabulary_statistics()
        print("Vocabulary:")
        print(f"  Total words: {vocab_stats['total_words']}")
        print(f"  Average frequency: {vocab_stats['avg_frequency']:.1f}")
        print(f"  Languages: {', '.join(vocab_stats['languages'])}")
        print()
        
        # Unknown words statistics
        unknown_stats = unknown_repo.get_unknown_words_statistics()
        print("Unknown Words:")
        print(f"  Total unknown: {unknown_stats['total_unknown']}")
        print(f"  Total frequency: {unknown_stats['total_frequency']}")
        print(f"  Average frequency: {unknown_stats['avg_frequency']:.1f}")
        print()
        
        # Categories
        categories = category_repo.get_all_categories()
        print(f"Categories: {len(categories)}")
        for category in categories[:5]:  # Show first 5
            word_count = len(category_repo.get_words_in_category(category['id']))
            print(f"  - {category['name']}: {word_count} words")
        if len(categories) > 5:
            print(f"  ... and {len(categories) - 5} more")
        print()
        
        # Recent activity
        recent_sessions = progress_repo.get_recent_sessions(limit=5)
        print(f"Recent Sessions: {len(recent_sessions)}")
        for session in recent_sessions:
            print(f"  - {session['session_type']} ({session['created_at'][:10]})")
        
        return 0
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return 1


def backup_database(args):
    """Create a backup of the database."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        db_manager = DatabaseManager(db_path)
        backup_path = db_manager.backup_database(args.backup_path)
        
        print(f"Database backed up to: {backup_path}")
        
        # Show backup size
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"Backup size: {backup_size:.2f} MB")
        
        return 0
    except Exception as e:
        print(f"Error creating backup: {e}")
        return 1


def search_words(args):
    """Search for words in the database."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        db_manager = DatabaseManager(db_path)
        vocab_repo = VocabularyRepository(db_manager)
        unknown_repo = UnknownWordsRepository(db_manager)
        
        query = args.query
        limit = args.limit
        
        print(f"Searching for '{query}'...")
        print()
        
        # Search vocabulary
        vocab_results = vocab_repo.search_words(query, limit=limit)
        if vocab_results:
            print(f"Vocabulary ({len(vocab_results)} results):")
            for word in vocab_results:
                print(f"  {word['word']} (freq: {word['frequency']}, level: {word['difficulty_level'] or 'N/A'})")
            print()
        
        # Search unknown words
        unknown_results = unknown_repo.search_unknown_words(query, limit=limit)
        if unknown_results:
            print(f"Unknown Words ({len(unknown_results)} results):")
            for word in unknown_results:
                print(f"  {word['word']} (freq: {word['frequency']})")
            print()
        
        if not vocab_results and not unknown_results:
            print("No results found.")
        
        return 0
    except Exception as e:
        print(f"Error searching: {e}")
        return 1


def vacuum_database(args):
    """Vacuum the database to reclaim space."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        # Get size before vacuum
        size_before = os.path.getsize(db_path) / (1024 * 1024)
        
        db_manager = DatabaseManager(db_path)
        db_manager.vacuum_database()
        
        # Get size after vacuum
        size_after = os.path.getsize(db_path) / (1024 * 1024)
        space_saved = size_before - size_after
        
        print("Database vacuumed successfully")
        print(f"Size before: {size_before:.2f} MB")
        print(f"Size after: {size_after:.2f} MB")
        print(f"Space saved: {space_saved:.2f} MB")
        
        return 0
    except Exception as e:
        print(f"Error vacuuming database: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='A1Decider Database Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create                     # Create new database
  %(prog)s migrate --source-dir .     # Migrate from current directory
  %(prog)s stats                      # Show database statistics
  %(prog)s search "haus"              # Search for words containing "haus"
  %(prog)s backup                     # Create database backup
  %(prog)s vacuum                     # Vacuum database
"""
    )
    
    parser.add_argument(
        '--database', '-d',
        help='Database file path (default: from config)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new database')
    create_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force recreation if database exists'
    )
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate data from flat files')
    migrate_parser.add_argument(
        '--source-dir', '-s',
        help='Source directory containing flat files (default: current directory)'
    )
    migrate_parser.add_argument(
        '--backup', '-b',
        action='store_true',
        help='Create backup before migration'
    )
    migrate_parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for migration (default: 1000)'
    )
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument(
        '--backup-path',
        help='Custom backup file path'
    )
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for words')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument(
        '--limit', '-l',
        type=int,
        default=20,
        help='Maximum number of results (default: 20)'
    )
    
    # Vacuum command
    subparsers.add_parser('vacuum', help='Vacuum database to reclaim space')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Command dispatch
    commands = {
        'create': create_database,
        'migrate': migrate_data,
        'stats': show_stats,
        'backup': backup_database,
        'search': search_words,
        'vacuum': vacuum_database,
    }
    
    if args.command in commands:
        return commands[args.command](args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())