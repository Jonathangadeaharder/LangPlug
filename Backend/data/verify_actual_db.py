#!/usr/bin/env python3
"""
Comprehensive vocabulary database verification script for actual schema.
Verifies import success, data integrity, and production readiness.
"""

import os
import sqlite3
import sys


def connect_to_database(db_path: str) -> sqlite3.Connection:
    """Connect to the SQLite database with proper settings."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        # Test connectivity
        conn.execute("SELECT 1").fetchone()
        return conn
    except sqlite3.Error:
        sys.exit(1)


def verify_database_integrity(conn: sqlite3.Connection) -> bool:
    """Run database integrity checks."""
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result[0] == "ok"
    except sqlite3.Error:
        return False


def examine_schema(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Examine and display database schema."""

    tables = {}
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for table_row in cursor.fetchall():
        table_name = table_row[0]

        # Get row count for each table
        # Safe: table_name from sqlite_master system table, not user input
        cursor2 = conn.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
        cursor2.fetchone()[0]

        # Get table structure
        # Safe: table_name from sqlite_master system table, not user input
        cursor2 = conn.execute(f"PRAGMA table_info({table_name})")
        for col in cursor2.fetchall():
            col_info = f"  {col[1]} ({col[2]})" + (" NOT NULL" if col[3] else "") + (" PRIMARY KEY" if col[5] else "")
            columns.append(col_info)
        tables[table_name] = columns

    return tables


def count_entries_by_level(conn: sqlite3.Connection) -> dict[str, int]:
    """Count vocabulary entries by CEFR level using actual schema."""

    counts = {}
    total = 0

    try:
        # Count by difficulty_level in vocabulary table
        cursor = conn.execute("""
            SELECT difficulty_level, COUNT(*) as count
            FROM vocabulary
            WHERE difficulty_level IS NOT NULL
            GROUP BY difficulty_level
            ORDER BY difficulty_level
        """)

        for row in cursor.fetchall():
            level = row[0]
            count = row[1]
            counts[level] = count
            total += count

        # Also verify using associations
        cursor = conn.execute("""
            SELECT wc.name, COUNT(DISTINCT wca.word_id) as count
            FROM word_category_associations wca
            JOIN word_categories wc ON wca.category_id = wc.id
            GROUP BY wc.name
            ORDER BY wc.name
        """)

        association_counts = {}
        association_total = 0
        for row in cursor.fetchall():
            level = row[0]
            count = row[1]
            association_counts[level] = count
            association_total += count

        # Compare the two methods
        if total == association_total:
            pass
        else:
            pass

        return counts

    except sqlite3.Error:
        return {}


def check_data_quality(conn: sqlite3.Connection) -> dict[str, any]:
    """Perform comprehensive data quality checks using actual schema."""

    issues = []
    stats = {}

    try:
        # Check for NULL values in critical fields
        cursor = conn.execute("""
            SELECT
                SUM(CASE WHEN word IS NULL OR word = '' THEN 1 ELSE 0 END) as null_word,
                SUM(CASE WHEN lemma IS NULL OR lemma = '' THEN 1 ELSE 0 END) as null_lemma,
                SUM(CASE WHEN difficulty_level IS NULL OR difficulty_level = '' THEN 1 ELSE 0 END) as null_level,
                SUM(CASE WHEN language IS NULL OR language = '' THEN 1 ELSE 0 END) as null_language
            FROM vocabulary
        """)
        row = cursor.fetchone()

        if row[0] == 0:
            pass
        else:
            issues.append(f"Found {row[0]} NULL/empty word entries")

        if row[1] == 0:
            pass
        else:
            issues.append(f"Found {row[1]} NULL/empty lemma entries")

        if row[2] == 0:
            pass
        else:
            issues.append(f"Found {row[2]} NULL/empty difficulty levels")

        if row[3] == 0:
            pass
        else:
            issues.append(f"Found {row[3]} NULL/empty language entries")

        # Check for duplicate German words
        cursor = conn.execute("""
            SELECT word, COUNT(*) as count
            FROM vocabulary
            GROUP BY LOWER(word)
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        duplicates = cursor.fetchall()

        if not duplicates:
            pass
        else:
            for _dup in duplicates[:5]:  # Show first 5
                pass

        # Check language distribution
        cursor = conn.execute("""
            SELECT language, COUNT(*) as count
            FROM vocabulary
            GROUP BY language
            ORDER BY count DESC
        """)

        for row in cursor.fetchall():
            row[0] or "NULL"
            row[1]

        # Check character encoding (look for German special characters)
        cursor = conn.execute("""
            SELECT
                SUM(CASE WHEN word LIKE '%ä%' OR word LIKE '%ö%' OR word LIKE '%ü%' OR word LIKE '%ß%' OR word LIKE '%Ä%' OR word LIKE '%Ö%' OR word LIKE '%Ü%' THEN 1 ELSE 0 END) as german_special,
                COUNT(*) as total
            FROM vocabulary
        """)
        row = cursor.fetchone()

        german_special_pct = (row[0] / row[1]) * 100 if row[1] > 0 else 0

        if german_special_pct > 3:  # We expect some German special chars
            pass
        else:
            issues.append("Suspiciously low German special character count - encoding issue?")

        # Check CEFR level distribution
        cursor = conn.execute("""
            SELECT difficulty_level, COUNT(*) as count,
                   COUNT(*) * 100.0 / (SELECT COUNT(*) FROM vocabulary) as percentage
            FROM vocabulary
            GROUP BY difficulty_level
            ORDER BY difficulty_level
        """)

        for row in cursor.fetchall():
            row[0] or "NULL"
            row[1]
            row[2]

        stats["issues"] = issues
        stats["duplicates"] = len(duplicates)
        stats["german_special_pct"] = german_special_pct

        return stats

    except sqlite3.Error as e:
        return {"error": str(e)}


def verify_relationships(conn: sqlite3.Connection) -> bool:
    """Verify foreign key relationships and table integrity."""

    try:
        # Check word_categories table
        cursor = conn.execute("SELECT name, COUNT(*) FROM word_categories GROUP BY name ORDER BY name")
        categories = cursor.fetchall()

        expected_levels = {"A1", "A2", "B1", "B2", "C1"}
        found_levels = {row[0] for row in categories}

        if expected_levels == found_levels:
            for _name, _count in categories:
                pass
        else:
            missing = expected_levels - found_levels
            extra = found_levels - expected_levels
            if missing:
                pass
            if extra:
                pass

        # Check associations integrity
        cursor = conn.execute("""
            SELECT COUNT(*) as total_associations,
                   COUNT(DISTINCT word_id) as unique_vocab,
                   COUNT(DISTINCT category_id) as unique_categories
            FROM word_category_associations
        """)
        cursor.fetchone()

        # Check for orphaned associations
        cursor = conn.execute("""
            SELECT COUNT(*)
            FROM word_category_associations wca
            LEFT JOIN vocabulary v ON wca.word_id = v.id
            WHERE v.id IS NULL
        """)
        orphaned_vocab = cursor.fetchone()[0]

        cursor = conn.execute("""
            SELECT COUNT(*)
            FROM word_category_associations wca
            LEFT JOIN word_categories wc ON wca.category_id = wc.id
            WHERE wc.id IS NULL
        """)
        orphaned_categories = cursor.fetchone()[0]

        return bool(orphaned_vocab == 0 and orphaned_categories == 0)

    except sqlite3.Error:
        return False


def sample_data_validation(conn: sqlite3.Connection, samples_per_level: int = 5) -> dict[str, list]:
    """Query and validate sample entries from each CEFR level."""

    samples = {}

    try:
        # Get samples from each level using difficulty_level
        cursor = conn.execute("""
            SELECT DISTINCT difficulty_level
            FROM vocabulary
            WHERE difficulty_level IS NOT NULL
            ORDER BY difficulty_level
        """)
        levels = [row[0] for row in cursor.fetchall()]

        for level in levels:
            cursor = conn.execute(
                """
                SELECT word, lemma, word_type, language
                FROM vocabulary
                WHERE difficulty_level = ?
                ORDER BY RANDOM()
                LIMIT ?
            """,
                (level, samples_per_level),
            )

            level_samples = []
            for _i, row in enumerate(cursor.fetchall(), 1):
                word = row[0]
                lemma = row[1]
                word_type = row[2] or "N/A"
                language = row[3]

                level_samples.append({"word": word, "lemma": lemma, "word_type": word_type, "language": language})

            samples[level] = level_samples

        return samples

    except sqlite3.Error:
        return {}


def check_missing_translations(conn: sqlite3.Connection) -> None:
    """Check what's missing for complete vocabulary system."""

    try:
        # Check if there's any Spanish translation data
        cursor = conn.execute("""
            SELECT COUNT(*) FROM vocabulary WHERE language = 'es'
        """)
        spanish_count = cursor.fetchone()[0]

        cursor = conn.execute("""
            SELECT COUNT(*) FROM vocabulary WHERE language = 'de'
        """)
        cursor.fetchone()[0]

        if spanish_count == 0:
            pass
        else:
            pass

        # Check for any additional translation tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%translation%'")
        translation_tables = cursor.fetchall()

        if translation_tables:
            for _table in translation_tables:
                pass
        else:
            pass

    except sqlite3.Error:
        pass


def performance_testing(conn: sqlite3.Connection) -> dict[str, float]:
    """Test query performance for common database operations."""

    import time

    results = {}

    try:
        # Test 1: Simple vocabulary lookup
        start_time = time.time()
        cursor = conn.execute("SELECT * FROM vocabulary WHERE word = 'Haus'")
        cursor.fetchall()
        results["simple_lookup"] = time.time() - start_time

        # Test 2: Level-based query
        start_time = time.time()
        cursor = conn.execute("""
            SELECT word, lemma
            FROM vocabulary
            WHERE difficulty_level = 'A1'
            LIMIT 100
        """)
        cursor.fetchall()
        results["level_query"] = time.time() - start_time

        # Test 3: Search query
        start_time = time.time()
        cursor = conn.execute("""
            SELECT word, lemma
            FROM vocabulary
            WHERE word LIKE 'haus%'
            LIMIT 50
        """)
        cursor.fetchall()
        results["search_query"] = time.time() - start_time

        # Test 4: Join query
        start_time = time.time()
        cursor = conn.execute("""
            SELECT v.word, wc.name
            FROM vocabulary v
            JOIN word_category_associations wca ON v.id = wca.word_id
            JOIN word_categories wc ON wca.category_id = wc.id
            WHERE wc.name = 'A1'
            LIMIT 100
        """)
        cursor.fetchall()
        results["join_query"] = time.time() - start_time

        # Test 5: Count query
        start_time = time.time()
        cursor = conn.execute("SELECT COUNT(*) FROM vocabulary")
        cursor.fetchone()
        results["count_query"] = time.time() - start_time

        # Check if indexes exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = cursor.fetchall()

        if indexes:
            for _idx in indexes:
                pass
        else:
            pass

        return results

    except sqlite3.Error:
        return {}


def compare_with_expected_counts(actual_counts: dict[str, int]) -> None:
    """Compare actual counts with expected counts from CSV files."""

    expected_counts = {"A1": 717, "A2": 581, "B1": 959, "B2": 1413, "C1": 2482}

    total_expected = sum(expected_counts.values())
    total_actual = sum(actual_counts.values())

    if abs(total_actual - total_expected) <= 10:  # Allow small variance
        pass
    else:
        pass

    for level in ["A1", "A2", "B1", "B2", "C1"]:
        expected = expected_counts.get(level, 0)
        actual = actual_counts.get(level, 0)
        diff = actual - expected

        "✅" if abs(diff) <= 5 else "⚠️ " if abs(diff) <= 50 else "❌"


def generate_final_report(
    counts: dict[str, int], quality_stats: dict[str, any], performance_results: dict[str, float], relationship_ok: bool
) -> None:
    """Generate final verification report."""

    total_entries = sum(counts.values())

    # Overall status
    critical_issues = len(quality_stats.get("issues", []))
    has_spanish = False  # We determined there are no Spanish translations

    if performance_results:
        sum(performance_results.values()) / len(performance_results)

    # Determine overall status
    if (
        not has_spanish
        or (critical_issues == 0 and relationship_ok and total_entries > 5000)
        or (critical_issues <= 2 and relationship_ok and total_entries > 4000)
    ):
        pass
    else:
        pass

    if not has_spanish:
        pass

    if quality_stats.get("duplicates", 0) > 0:
        pass

    if quality_stats.get("german_special_pct", 0) < 3:
        pass

    if not relationship_ok:
        pass

    if any(time > 0.05 for time in performance_results.values()):
        pass

    if total_entries > 6000 and critical_issues == 0:
        pass


def main():
    """Main verification function."""

    db_path = "/mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/Backend/data/langplug.db"

    if not os.path.exists(db_path):
        sys.exit(1)

    # Connect to database
    conn = connect_to_database(db_path)

    try:
        # Run all verification steps
        verify_database_integrity(conn)
        examine_schema(conn)
        counts = count_entries_by_level(conn)
        quality_stats = check_data_quality(conn)
        relationship_ok = verify_relationships(conn)
        sample_data_validation(conn)
        check_missing_translations(conn)
        performance_results = performance_testing(conn)

        # Compare with expected counts
        compare_with_expected_counts(counts)

        # Generate final report
        generate_final_report(counts, quality_stats, performance_results, relationship_ok)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
