#!/usr/bin/env python3
"""
Data Migration Script for A1Decider Database

Migrates data from flat files (JSON, TXT) to SQLite database.
Handles vocabulary lists, unknown words, and creates initial categories.
"""

import os
import json
import logging
from typing import Dict, List, Set, Any, Optional
from pathlib import Path
import re

from database_manager import DatabaseManager
from repositories.vocabulary_repository import VocabularyRepository
from repositories.unknown_words_repository import UnknownWordsRepository
from repositories.word_category_repository import WordCategoryRepository
from repositories.user_progress_repository import UserProgressRepository


class DataMigration:
    """Handles migration of data from flat files to database."""
    
    def __init__(self, db_path: str, source_directory: str):
        """
        Initialize the data migration.
        
        Args:
            db_path: Path to the SQLite database file
            source_directory: Directory containing the flat files to migrate
        """
        self.db_path = db_path
        self.source_dir = Path(source_directory)
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize repositories
        self.vocab_repo = VocabularyRepository(self.db_manager)
        self.unknown_repo = UnknownWordsRepository(self.db_manager)
        self.category_repo = WordCategoryRepository(self.db_manager)
        self.progress_repo = UserProgressRepository(self.db_manager)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def run_migration(self, backup_existing: bool = True) -> Dict[str, Any]:
        """
        Run the complete data migration process.
        
        Args:
            backup_existing: Whether to backup existing database
            
        Returns:
            Migration results summary
        """
        self.logger.info("Starting A1Decider data migration...")
        
        results = {
            'success': False,
            'vocabulary_migrated': 0,
            'unknown_words_migrated': 0,
            'categories_created': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Backup existing database if requested
            if backup_existing and os.path.exists(self.db_path):
                self._backup_database()
            
            # Initialize database
            self.db_manager.create_database()
            
            # Create processing session for migration
            session_id = self.progress_repo.create_processing_session(
                session_type='data_migration',
                source_file=str(self.source_dir),
                metadata={'migration_version': '1.0.0'}
            )
            
            # Migrate data
            results['unknown_words_migrated'] = self._migrate_unknown_words()
            results['vocabulary_migrated'] = self._migrate_vocabulary_files()
            results['categories_created'] = self._create_word_categories()
            
            # End migration session
            total_words = results['vocabulary_migrated'] + results['unknown_words_migrated']
            self.progress_repo.end_processing_session(
                session_id, 
                words_processed=total_words,
                new_words_discovered=results['vocabulary_migrated']
            )
            
            results['success'] = True
            self.logger.info(f"Migration completed successfully: {results}")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            results['errors'].append(str(e))
            results['success'] = False
        
        return results
    
    def _backup_database(self) -> str:
        """
        Create a backup of the existing database.
        
        Returns:
            Path to the backup file
        """
        backup_path = self.db_manager.backup_database()
        self.logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    
    def _migrate_unknown_words(self) -> int:
        """
        Migrate unknown words from globalunknowns.json.
        
        Returns:
            Number of unknown words migrated
        """
        self.logger.info("Migrating unknown words...")
        
        unknown_words_file = self.source_dir / 'globalunknowns.json'
        if not unknown_words_file.exists():
            self.logger.warning(f"Unknown words file not found: {unknown_words_file}")
            return 0
        
        try:
            with open(unknown_words_file, 'r', encoding='utf-8') as f:
                unknown_words_data = json.load(f)
            
            migrated_count = 0
            
            for word, frequency in unknown_words_data.items():
                if isinstance(word, str) and word.strip():
                    # Clean and validate word
                    clean_word = word.strip().lower()
                    if self._is_valid_word(clean_word):
                        self.unknown_repo.add_unknown_word(
                            word=clean_word,
                            frequency=int(frequency) if isinstance(frequency, (int, float)) else 1,
                            language='de'
                        )
                        migrated_count += 1
            
            self.logger.info(f"Migrated {migrated_count} unknown words")
            return migrated_count
            
        except Exception as e:
            self.logger.error(f"Error migrating unknown words: {str(e)}")
            return 0
    
    def _migrate_vocabulary_files(self) -> int:
        """
        Migrate vocabulary from text files.
        
        Returns:
            Number of vocabulary words migrated
        """
        self.logger.info("Migrating vocabulary files...")
        
        vocabulary_files = [
            'vocabulary.txt',
            'giuliwords.txt',
            'charaktere.txt'
        ]
        
        migrated_count = 0
        
        for filename in vocabulary_files:
            file_path = self.source_dir / filename
            if file_path.exists():
                count = self._migrate_vocabulary_file(file_path, filename)
                migrated_count += count
                self.logger.info(f"Migrated {count} words from {filename}")
            else:
                self.logger.warning(f"Vocabulary file not found: {file_path}")
        
        return migrated_count
    
    def _migrate_vocabulary_file(self, file_path: Path, source_file: str) -> int:
        """
        Migrate vocabulary from a single text file.
        
        Args:
            file_path: Path to the vocabulary file
            source_file: Name of the source file for categorization
            
        Returns:
            Number of words migrated from this file
        """
        migrated_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Determine file format and category
            category_name = self._get_category_for_file(source_file)
            category_id = None
            
            if category_name:
                category_id = self.category_repo.create_category(
                    name=category_name,
                    description=f"Words from {source_file}",
                    language='de'
                )
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse line based on format
                word_data = self._parse_vocabulary_line(line)
                if word_data:
                    word_id = self._add_vocabulary_word(word_data)
                    if word_id and category_id:
                        self.category_repo.associate_word_with_category(word_id, category_id)
                    migrated_count += 1
            
        except Exception as e:
            self.logger.error(f"Error migrating {file_path}: {str(e)}")
        
        return migrated_count
    
    def _parse_vocabulary_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a line from a vocabulary file.
        
        Args:
            line: Line from vocabulary file
            
        Returns:
            Dictionary with word data or None if invalid
        """
        # Handle different formats:
        # Format 1: "word frequency" (vocabulary.txt)
        # Format 2: "word" (giuliwords.txt, charaktere.txt)
        
        parts = line.split()
        if not parts:
            return None
        
        word = parts[0].lower().strip()
        if not self._is_valid_word(word):
            return None
        
        word_data = {
            'word': word,
            'language': 'de',
            'frequency': 1,
            'difficulty_level': 'unknown'
        }
        
        # Try to extract frequency if present
        if len(parts) > 1 and parts[1].isdigit():
            word_data['frequency'] = int(parts[1])
        
        # Estimate difficulty based on word length and frequency
        word_data['difficulty_level'] = self._estimate_difficulty(word, word_data['frequency'])
        
        return word_data
    
    def _add_vocabulary_word(self, word_data: Dict[str, Any]) -> Optional[int]:
        """
        Add a vocabulary word to the database.
        
        Args:
            word_data: Dictionary with word information
            
        Returns:
            Word ID if successful, None otherwise
        """
        try:
            return self.vocab_repo.add_word(
                word=word_data['word'],
                frequency=word_data.get('frequency', 1),
                difficulty_level=word_data.get('difficulty_level', 'unknown'),
                language=word_data.get('language', 'de')
            )
        except Exception as e:
            self.logger.warning(f"Could not add word '{word_data['word']}': {str(e)}")
            return None
    
    def _get_category_for_file(self, filename: str) -> Optional[str]:
        """
        Get appropriate category name for a vocabulary file.
        
        Args:
            filename: Name of the vocabulary file
            
        Returns:
            Category name or None
        """
        category_mapping = {
            'vocabulary.txt': 'General Vocabulary',
            'giuliwords.txt': 'Giulia Words',
            'charaktere.txt': 'Character Names'
        }
        
        return category_mapping.get(filename)
    
    def _create_word_categories(self) -> int:
        """
        Create additional word categories based on migrated data.
        
        Returns:
            Number of categories created
        """
        self.logger.info("Creating word categories...")
        
        # Additional categories beyond the default ones in schema.sql
        additional_categories = [
            ('High Frequency', 'Words that appear very frequently in texts'),
            ('Medium Frequency', 'Words that appear moderately in texts'),
            ('Low Frequency', 'Words that appear rarely in texts'),
            ('Migrated Data', 'Words migrated from flat files'),
            ('Needs Review', 'Words that need manual review and categorization')
        ]
        
        created_count = 0
        
        for name, description in additional_categories:
            try:
                category_id = self.category_repo.create_category(
                    name=name,
                    description=description,
                    language='de'
                )
                if category_id:
                    created_count += 1
            except Exception as e:
                self.logger.warning(f"Could not create category '{name}': {str(e)}")
        
        # Categorize words by frequency
        self._categorize_words_by_frequency()
        
        return created_count
    
    def _categorize_words_by_frequency(self):
        """
        Automatically categorize words based on their frequency.
        """
        try:
            # Get frequency categories
            high_freq_id = self.category_repo.get_category_id('High Frequency')
            medium_freq_id = self.category_repo.get_category_id('Medium Frequency')
            low_freq_id = self.category_repo.get_category_id('Low Frequency')
            
            if not all([high_freq_id, medium_freq_id, low_freq_id]):
                return
            
            # Get all vocabulary words
            all_words = self.vocab_repo.get_all_words()
            
            for word in all_words:
                frequency = word.get('frequency', 0)
                word_id = word['id']
                
                # Categorize based on frequency thresholds
                if frequency >= 10:
                    self.category_repo.associate_word_with_category(word_id, high_freq_id)
                elif frequency >= 3:
                    self.category_repo.associate_word_with_category(word_id, medium_freq_id)
                else:
                    self.category_repo.associate_word_with_category(word_id, low_freq_id)
        
        except Exception as e:
            self.logger.warning(f"Error categorizing words by frequency: {str(e)}")
    
    def _is_valid_word(self, word: str) -> bool:
        """
        Check if a word is valid for migration.
        
        Args:
            word: Word to validate
            
        Returns:
            True if word is valid, False otherwise
        """
        if not word or len(word) < 2:
            return False
        
        # Check for valid characters (letters, hyphens, apostrophes)
        if not re.match(r"^[a-zA-ZäöüßÄÖÜ'-]+$", word):
            return False
        
        # Exclude common non-words
        excluded_patterns = [
            r'^\d+$',  # Pure numbers
            r'^[^a-zA-ZäöüßÄÖÜ]+$',  # No letters
            r'^.{1}$',  # Single character
        ]
        
        for pattern in excluded_patterns:
            if re.match(pattern, word):
                return False
        
        return True
    
    def _estimate_difficulty(self, word: str, frequency: int) -> str:
        """
        Estimate difficulty level based on word characteristics.
        
        Args:
            word: The word to analyze
            frequency: Word frequency
            
        Returns:
            Estimated difficulty level
        """
        # Simple heuristic based on length and frequency
        word_length = len(word)
        
        if frequency >= 10 and word_length <= 6:
            return 'beginner'
        elif frequency >= 5 or (frequency >= 2 and word_length <= 8):
            return 'intermediate'
        elif word_length > 12 or frequency == 1:
            return 'advanced'
        else:
            return 'intermediate'
    
    def generate_migration_report(self) -> str:
        """
        Generate a detailed migration report.
        
        Returns:
            Migration report as string
        """
        report_lines = [
            "A1Decider Database Migration Report",
            "=" * 40,
            ""
        ]
        
        # Database statistics
        vocab_stats = self.vocab_repo.get_vocabulary_stats()
        unknown_stats = self.unknown_repo.get_unknown_words_stats()
        
        report_lines.extend([
            "Database Statistics:",
            f"- Total vocabulary words: {vocab_stats.get('total_words', 0)}",
            f"- Total unknown words: {unknown_stats.get('total_unknown_words', 0)}",
            f"- Average word frequency: {vocab_stats.get('average_frequency', 0):.2f}",
            f"- Categories created: {len(self.category_repo.get_all_categories())}",
            ""
        ])
        
        # Difficulty distribution
        if 'difficulty_distribution' in vocab_stats:
            report_lines.append("Difficulty Distribution:")
            for level, count in vocab_stats['difficulty_distribution'].items():
                report_lines.append(f"- {level.title()}: {count} words")
            report_lines.append("")
        
        # Category statistics
        popular_categories = self.category_repo.get_popular_categories(limit=5)
        if popular_categories:
            report_lines.append("Top Categories by Word Count:")
            for category in popular_categories:
                report_lines.append(f"- {category['name']}: {category['word_count']} words")
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "Recommendations:",
            "- Review words with 'unknown' difficulty level",
            "- Add definitions and example sentences for vocabulary",
            "- Create more specific categories for better organization",
            "- Set up regular backup schedule for the database",
            ""
        ])
        
        return "\n".join(report_lines)


def main():
    """Main migration function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate A1Decider data to database')
    parser.add_argument('--db-path', required=True, help='Path to SQLite database file')
    parser.add_argument('--source-dir', required=True, help='Directory containing flat files')
    parser.add_argument('--backup', action='store_true', help='Backup existing database')
    parser.add_argument('--report', action='store_true', help='Generate migration report')
    
    args = parser.parse_args()
    
    # Run migration
    migration = DataMigration(args.db_path, args.source_dir)
    results = migration.run_migration(backup_existing=args.backup)
    
    print(f"Migration completed: {results}")
    
    # Generate report if requested
    if args.report:
        report = migration.generate_migration_report()
        report_file = Path(args.db_path).parent / 'migration_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Migration report saved to: {report_file}")


if __name__ == '__main__':
    main()