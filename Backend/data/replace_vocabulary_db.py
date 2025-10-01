#!/usr/bin/env python3
"""
Comprehensive script to replace vocabulary database content with cleaned CSV files.

This script will:
1. Backup the existing database
2. Clear all vocabulary-related data
3. Import vocabulary from cleaned CSV files with proper CEFR levels
4. Verify the import process
5. Provide detailed logging
"""

import csv
import logging
import os
import shutil
import sqlite3
import sys
from datetime import datetime


class VocabularyDatabaseReplacer:
    """Handle the complete replacement of vocabulary data in the database."""

    def __init__(self, db_path: str, csv_dir: str):
        """Initialize the database replacer."""
        self.db_path = db_path
        self.csv_dir = csv_dir
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("vocabulary_import.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

        # CSV file mapping to CEFR levels
        self.csv_files = {
            "A1_vokabeln.csv": "A1",
            "A2_vokabeln.csv": "A2",
            "B1_vokabeln.csv": "B1",
            "B2_vokabeln.csv": "B2",
            "C1_vokabeln.csv": "C1",
        }

    def backup_database(self) -> bool:
        """Create a backup of the existing database."""
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.backup_path)
                self.logger.info(f"Database backed up to: {self.backup_path}")
                return True
            else:
                self.logger.warning(f"Database file not found: {self.db_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False

    def connect_database(self) -> sqlite3.Connection:
        """Connect to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            return conn
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def clear_vocabulary_data(self, conn: sqlite3.Connection) -> bool:
        """Clear all vocabulary-related data from the database."""
        try:
            cursor = conn.cursor()

            # Clear tables in order (respecting foreign key constraints)
            tables_to_clear = [
                "session_word_discoveries",
                "user_learning_progress",
                "word_category_associations",
                "unknown_words",
                "vocabulary",
                "word_categories",
                "processing_sessions",
            ]

            for table in tables_to_clear:
                # Safe: table names are from hardcoded whitelist, not user input
                cursor.execute(f"DELETE FROM {table}")  # noqa: S608
                deleted_count = cursor.rowcount
                self.logger.info(f"Cleared {deleted_count} records from {table}")

            # Reset auto-increment counters (if sqlite_sequence table exists)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
            if cursor.fetchone():
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('vocabulary', 'word_categories')")

            conn.commit()
            self.logger.info("Successfully cleared all vocabulary-related data")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear vocabulary data: {e}")
            conn.rollback()
            return False

    def read_csv_file(self, csv_path: str) -> list[tuple[str, str]]:
        """Read vocabulary data from CSV file."""
        vocabulary_data = []

        try:
            with open(csv_path, encoding="utf-8") as file:
                reader = csv.reader(file)

                # Skip header row
                header = next(reader, None)
                if header:
                    self.logger.info(f"CSV header: {header}")

                for row_num, row in enumerate(reader, 2):  # Start from row 2 (after header)
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        german_word = row[0].strip()
                        spanish_translation = row[1].strip()
                        vocabulary_data.append((german_word, spanish_translation))
                    elif len(row) >= 1 and row[0].strip():
                        # Log rows with missing Spanish translation
                        self.logger.warning(f"Row {row_num} in {csv_path} missing Spanish translation: {row}")

            self.logger.info(f"Read {len(vocabulary_data)} vocabulary entries from {csv_path}")
            return vocabulary_data

        except Exception as e:
            self.logger.error(f"Failed to read CSV file {csv_path}: {e}")
            return []

    def create_word_category(self, conn: sqlite3.Connection, level: str, file_path: str) -> int:
        """Create a word category for the CEFR level."""
        try:
            cursor = conn.cursor()

            # Insert the category
            cursor.execute(
                """
                INSERT INTO word_categories (name, description, file_path, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (level, f"CEFR Level {level} Vocabulary", file_path, True, datetime.now(), datetime.now()),
            )

            category_id = cursor.lastrowid
            self.logger.info(f"Created word category: {level} (ID: {category_id})")
            return category_id

        except Exception as e:
            self.logger.error(f"Failed to create word category {level}: {e}")
            raise

    def insert_vocabulary_batch(
        self, conn: sqlite3.Connection, vocabulary_data: list[tuple[str, str]], level: str, category_id: int
    ) -> int:
        """Insert vocabulary data in batches for better performance."""
        try:
            cursor = conn.cursor()

            # Prepare vocabulary records
            vocabulary_records = []
            category_association_records = []
            current_time = datetime.now()

            for german_word, _spanish_translation in vocabulary_data:
                vocabulary_records.append(
                    (
                        german_word,
                        german_word,  # Using word as lemma for now
                        "de",  # German language
                        level,  # CEFR difficulty level
                        None,  # word_type (to be determined later)
                        current_time,
                        current_time,
                    )
                )

            # Insert vocabulary records
            cursor.executemany(
                """
                INSERT INTO vocabulary (word, lemma, language, difficulty_level, word_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                vocabulary_records,
            )

            # Get the starting ID for word_category_associations
            cursor.execute("SELECT last_insert_rowid()")
            last_id = cursor.fetchone()[0]
            first_id = last_id - len(vocabulary_records) + 1

            # Create category associations
            for i in range(len(vocabulary_records)):
                word_id = first_id + i
                category_association_records.append((word_id, category_id, current_time))

            # Insert category associations
            cursor.executemany(
                """
                INSERT INTO word_category_associations (word_id, category_id, created_at)
                VALUES (?, ?, ?)
            """,
                category_association_records,
            )

            inserted_count = len(vocabulary_records)
            self.logger.info(f"Inserted {inserted_count} vocabulary entries for level {level}")
            return inserted_count

        except Exception as e:
            self.logger.error(f"Failed to insert vocabulary for level {level}: {e}")
            raise

    def collect_all_vocabulary(self) -> dict[str, tuple[str, str, str]]:
        """Collect all vocabulary from CSV files, handling duplicates by keeping the lowest level."""
        all_vocabulary = {}  # word -> (spanish_translation, level, source_file)
        level_order = ["A1", "A2", "B1", "B2", "C1"]

        for csv_file, level in self.csv_files.items():
            csv_path = os.path.join(self.csv_dir, csv_file)

            if not os.path.exists(csv_path):
                self.logger.warning(f"CSV file not found: {csv_path}")
                continue

            vocabulary_data = self.read_csv_file(csv_path)

            for german_word, spanish_translation in vocabulary_data:
                if german_word in all_vocabulary:
                    # Check if current level is lower than existing level
                    existing_level = all_vocabulary[german_word][1]
                    if level_order.index(level) < level_order.index(existing_level):
                        # Replace with lower level
                        all_vocabulary[german_word] = (spanish_translation, level, csv_file)
                        self.logger.debug(f"Updated {german_word}: {existing_level} -> {level}")
                else:
                    all_vocabulary[german_word] = (spanish_translation, level, csv_file)

        self.logger.info(f"Collected {len(all_vocabulary)} unique vocabulary entries")
        return all_vocabulary

    def import_csv_data(self, conn: sqlite3.Connection) -> dict[str, int]:
        """Import all CSV files into the database, handling duplicates."""
        import_results = {}

        try:
            # First collect all vocabulary and resolve duplicates
            all_vocabulary = self.collect_all_vocabulary()

            # Group vocabulary by level
            vocabulary_by_level = {}
            for word, (translation, level, _source_file) in all_vocabulary.items():
                if level not in vocabulary_by_level:
                    vocabulary_by_level[level] = []
                vocabulary_by_level[level].append((word, translation))

            # Create categories and insert vocabulary for each level
            for level in self.csv_files.values():
                if level not in vocabulary_by_level:
                    self.logger.info(f"No vocabulary for level {level} after deduplication")
                    import_results[level] = 0
                    continue

                vocabulary_data = vocabulary_by_level[level]
                self.logger.info(f"Processing {len(vocabulary_data)} unique words for level {level}")

                # Create word category for this level
                category_id = self.create_word_category(conn, level, f"{level}_vocabulary")

                # Insert vocabulary data
                inserted_count = self.insert_vocabulary_batch(conn, vocabulary_data, level, category_id)
                import_results[level] = inserted_count

            conn.commit()
            self.logger.info("Successfully imported all CSV data")
            return import_results

        except Exception as e:
            self.logger.error(f"Failed to import CSV data: {e}")
            conn.rollback()
            raise

    def verify_import(self, conn: sqlite3.Connection, expected_results: dict[str, int]) -> bool:
        """Verify the import process by checking record counts."""
        try:
            cursor = conn.cursor()

            self.logger.info("=== Import Verification ===")

            # Check total vocabulary count
            cursor.execute("SELECT COUNT(*) FROM vocabulary")
            total_vocab = cursor.fetchone()[0]
            expected_total = sum(expected_results.values())

            self.logger.info(f"Total vocabulary entries: {total_vocab} (expected: {expected_total})")

            # Check counts by difficulty level
            for level, expected_count in expected_results.items():
                cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE difficulty_level = ?", (level,))
                actual_count = cursor.fetchone()[0]

                status = "✓" if actual_count == expected_count else "✗"
                self.logger.info(f"Level {level}: {actual_count} entries {status}")

                if actual_count != expected_count:
                    self.logger.warning(f"Mismatch in {level}: expected {expected_count}, got {actual_count}")

            # Check word categories
            cursor.execute("SELECT COUNT(*) FROM word_categories")
            category_count = cursor.fetchone()[0]
            self.logger.info(f"Word categories: {category_count}")

            # Check word-category associations
            cursor.execute("SELECT COUNT(*) FROM word_category_associations")
            association_count = cursor.fetchone()[0]
            self.logger.info(f"Word-category associations: {association_count}")

            # Sample some entries
            self.logger.info("Sample entries:")
            cursor.execute("""
                SELECT v.word, v.difficulty_level, wc.name
                FROM vocabulary v
                JOIN word_category_associations wca ON v.id = wca.word_id
                JOIN word_categories wc ON wca.category_id = wc.id
                ORDER BY v.difficulty_level, v.word
                LIMIT 10
            """)

            sample_entries = cursor.fetchall()
            for word, level, category in sample_entries:
                self.logger.info(f"  {word} ({level}) - {category}")

            return total_vocab == expected_total

        except Exception as e:
            self.logger.error(f"Failed to verify import: {e}")
            return False

    def run_replacement(self) -> bool:
        """Execute the complete vocabulary replacement process."""
        self.logger.info("=== Starting Vocabulary Database Replacement ===")

        try:
            # Step 1: Backup database
            if not self.backup_database():
                return False

            # Step 2: Connect to database
            conn = self.connect_database()

            try:
                # Step 3: Clear existing vocabulary data
                if not self.clear_vocabulary_data(conn):
                    return False

                # Step 4: Import CSV data
                import_results = self.import_csv_data(conn)

                # Step 5: Verify import
                if self.verify_import(conn, import_results):
                    self.logger.info("=== Vocabulary replacement completed successfully! ===")

                    # Print summary
                    total_imported = sum(import_results.values())
                    self.logger.info(f"Total vocabulary entries imported: {total_imported}")
                    for level, count in import_results.items():
                        self.logger.info(f"  {level}: {count} entries")

                    return True
                else:
                    self.logger.error("Import verification failed!")
                    return False

            finally:
                conn.close()

        except Exception as e:
            self.logger.error(f"Vocabulary replacement failed: {e}")
            return False


def main():
    """Main function to execute the vocabulary replacement."""
    # Configuration
    db_path = "/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/data/langplug.db"
    csv_dir = "/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/data"

    # Create and run the replacer
    replacer = VocabularyDatabaseReplacer(db_path, csv_dir)
    success = replacer.run_replacement()

    if success:
        pass
    else:
        pass

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
