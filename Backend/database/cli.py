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

from core.database import get_async_session, init_database
from database.migration import DataMigration
import asyncio
from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import AsyncSession
# Default database configuration
DEFAULT_DATABASE_PATH = "data/a1decider.db"


async def create_database_async(args):
    """Create a new database with schema."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if os.path.exists(db_path) and not args.force:
        print(f"Database already exists at {db_path}")
        print("Use --force to recreate the database")
        return 1
    
    try:
        # Initialize the database with async SQLAlchemy
        await init_database()
        print(f"Database created successfully at {db_path}")
        
        # Show basic database info
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"Database size: {size_mb:.2f} MB")
        
        return 0
    except Exception as e:
        print(f"Error creating database: {e}")
        return 1

def create_database(args):
    """Sync wrapper for create_database_async."""
    return asyncio.run(create_database_async(args))


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


async def show_stats_async(args):
    """Show database statistics."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        async with get_async_session() as session:
            print(f"Database Statistics for {db_path}")
            print("=" * 50)
            
            # Database info
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"Database size: {size_mb:.2f} MB")
            print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
            print()
            
            # Vocabulary statistics
            vocab_count = await session.execute(text("SELECT COUNT(*) FROM vocabulary"))
            total_words = vocab_count.scalar()
            
            avg_freq = await session.execute(text("SELECT AVG(frequency) FROM vocabulary WHERE frequency > 0"))
            avg_frequency = avg_freq.scalar() or 0
            
            languages = await session.execute(text("SELECT DISTINCT language FROM vocabulary WHERE language IS NOT NULL"))
            lang_list = [row[0] for row in languages.fetchall()]
            
            print("Vocabulary:")
            print(f"  Total words: {total_words}")
            print(f"  Average frequency: {avg_frequency:.1f}")
            print(f"  Languages: {', '.join(lang_list) if lang_list else 'None'}")
            print()
            
            # User progress statistics
            progress_count = await session.execute(text("SELECT COUNT(*) FROM user_learning_progress"))
            total_progress = progress_count.scalar()
            
            print("User Progress:")
            print(f"  Total progress entries: {total_progress}")
            print()
        
        return 0
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return 1

def show_stats(args):
    """Sync wrapper for show_stats_async."""
    return asyncio.run(show_stats_async(args))


def backup_database(args):
    """Create a backup of the database."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        import shutil
        from datetime import datetime
        
        # Create backup filename if not provided
        if args.backup_path:
            backup_path = args.backup_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{db_path}.backup_{timestamp}"
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        print(f"Database backed up to: {backup_path}")
        
        # Show backup size
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)
        print(f"Backup size: {backup_size:.2f} MB")
        
        return 0
    except Exception as e:
        print(f"Error creating backup: {e}")
        return 1


async def search_words_async(args):
    """Search for words in the database."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        async with get_async_session() as session:
            query = args.query
            limit = args.limit
            
            print(f"Searching for '{query}'...")
            print()
            
            # Search vocabulary
            vocab_query = text("""
                SELECT word, frequency, difficulty_level 
                FROM vocabulary 
                WHERE word LIKE :query 
                ORDER BY frequency DESC 
                LIMIT :limit
            """)
            vocab_results = await session.execute(vocab_query, {
                "query": f"%{query}%",
                "limit": limit
            })
            vocab_rows = vocab_results.fetchall()
            
            if vocab_rows:
                print(f"Vocabulary ({len(vocab_rows)} results):")
                for row in vocab_rows:
                    word, frequency, difficulty_level = row
                    print(f"  {word} (freq: {frequency}, level: {difficulty_level or 'N/A'})")
                print()
            
            # Search user progress
            progress_query = text("""
                SELECT DISTINCT word 
                FROM user_learning_progress 
                WHERE word LIKE :query 
                LIMIT :limit
            """)
            progress_results = await session.execute(progress_query, {
                "query": f"%{query}%",
                "limit": limit
            })
            progress_rows = progress_results.fetchall()
            
            if progress_rows:
                print(f"User Progress ({len(progress_rows)} results):")
                for row in progress_rows:
                    print(f"  {row[0]}")
                print()
            
            if not vocab_rows and not progress_rows:
                print("No results found.")
        
        return 0
    except Exception as e:
        print(f"Error searching: {e}")
        return 1

def search_words(args):
    """Sync wrapper for search_words_async."""
    return asyncio.run(search_words_async(args))


async def vacuum_database_async(args):
    """Vacuum the database to reclaim space."""
    db_path = args.database or DEFAULT_DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return 1
    
    try:
        # Get size before vacuum
        size_before = os.path.getsize(db_path) / (1024 * 1024)
        
        async with get_async_session() as session:
            await session.execute(text("VACUUM"))
            await session.commit()
        
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

def vacuum_database(args):
    """Sync wrapper for vacuum_database_async."""
    return asyncio.run(vacuum_database_async(args))


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