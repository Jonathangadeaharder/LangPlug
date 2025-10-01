#!/usr/bin/env python3
"""
Comprehensive vocabulary database verification script.
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

        # Get table structure
        columns = []
        cursor2 = conn.execute("PRAGMA table_info(" + table_name + ")")
        for col in cursor2.fetchall():
            col_info = f"  {col[1]} ({col[2]})" + (" NOT NULL" if col[3] else "") + (" PRIMARY KEY" if col[5] else "")
            columns.append(col_info)
        tables[table_name] = columns

    return tables


def count_entries_by_level(conn: sqlite3.Connection) -> dict[str, int]:
    """Count vocabulary entries by CEFR level."""

    counts = {}
    total = 0

    try:
        # Get all vocabulary entries with their levels
        cursor = conn.execute("""
            SELECT wc.level, COUNT(DISTINCT v.id) as count
            FROM vocabulary v
            JOIN word_category_associations wca ON v.id = wca.vocabulary_id
            JOIN word_categories wc ON wca.category_id = wc.id
            GROUP BY wc.level
            ORDER BY wc.level
        """)

        for row in cursor.fetchall():
            level = row[0]
            count = row[1]
            counts[level] = count
            total += count

        # Also get total unique vocabulary entries
        cursor = conn.execute("SELECT COUNT(*) FROM vocabulary")
        cursor.fetchone()[0]

        return counts

    except sqlite3.Error:
        return {}


def check_data_quality(conn: sqlite3.Connection) -> dict[str, any]:
    """Perform comprehensive data quality checks."""

    issues = []
    stats = {}

    try:
        # Check for NULL values in critical fields
        cursor = conn.execute("""
            SELECT
                SUM(CASE WHEN german_word IS NULL OR german_word = '' THEN 1 ELSE 0 END) as null_german,
                SUM(CASE WHEN spanish_translation IS NULL OR spanish_translation = '' THEN 1 ELSE 0 END) as null_spanish,
                SUM(CASE WHEN base_form IS NULL OR base_form = '' THEN 1 ELSE 0 END) as null_base_form
            FROM vocabulary
        """)
        row = cursor.fetchone()

        if row[0] == 0:
            pass
        else:
            issues.append(f"Found {row[0]} NULL/empty German words")

        if row[1] == 0:
            pass
        else:
            issues.append(f"Found {row[1]} NULL/empty Spanish translations")

        if row[2] == 0:
            pass
        else:
            issues.append(f"Found {row[2]} NULL/empty base forms")

        # Check for duplicate German words
        cursor = conn.execute("""
            SELECT german_word, COUNT(*) as count
            FROM vocabulary
            GROUP BY LOWER(german_word)
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

        # Check character encoding (look for special German/Spanish characters)
        cursor = conn.execute("""
            SELECT
                SUM(CASE WHEN german_word LIKE '%ä%' OR german_word LIKE '%ö%' OR german_word LIKE '%ü%' OR german_word LIKE '%ß%' THEN 1 ELSE 0 END) as german_special,
                SUM(CASE WHEN spanish_translation LIKE '%ñ%' OR spanish_translation LIKE '%á%' OR spanish_translation LIKE '%é%' OR spanish_translation LIKE '%í%' OR spanish_translation LIKE '%ó%' OR spanish_translation LIKE '%ú%' THEN 1 ELSE 0 END) as spanish_special,
                COUNT(*) as total
            FROM vocabulary
        """)
        row = cursor.fetchone()

        german_special_pct = (row[0] / row[2]) * 100 if row[2] > 0 else 0
        spanish_special_pct = (row[1] / row[2]) * 100 if row[2] > 0 else 0

        if german_special_pct > 5:  # We expect some German special chars
            pass
        else:
            issues.append("Suspiciously low German special character count - encoding issue?")

        stats["issues"] = issues
        stats["duplicates"] = len(duplicates)
        stats["german_special_pct"] = german_special_pct
        stats["spanish_special_pct"] = spanish_special_pct

        return stats

    except sqlite3.Error as e:
        return {"error": str(e)}


def verify_relationships(conn: sqlite3.Connection) -> bool:
    """Verify foreign key relationships and table integrity."""

    try:
        # Check word_categories table
        cursor = conn.execute("SELECT level, COUNT(*) FROM word_categories GROUP BY level ORDER BY level")
        categories = cursor.fetchall()

        expected_levels = {"A1", "A2", "B1", "B2", "C1"}
        found_levels = {row[0] for row in categories}

        if expected_levels == found_levels:
            for _level, _count in categories:
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
                   COUNT(DISTINCT vocabulary_id) as unique_vocab,
                   COUNT(DISTINCT category_id) as unique_categories
            FROM word_category_associations
        """)
        cursor.fetchone()

        # Check for orphaned associations
        cursor = conn.execute("""
            SELECT COUNT(*)
            FROM word_category_associations wca
            LEFT JOIN vocabulary v ON wca.vocabulary_id = v.id
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


def sample_data_validation(conn: sqlite3.Connection, samples_per_level: int = 3) -> dict[str, list]:
    """Query and validate sample entries from each CEFR level."""

    samples = {}

    try:
        # Get samples from each level
        cursor = conn.execute("""
            SELECT DISTINCT wc.level
            FROM word_categories wc
            ORDER BY wc.level
        """)
        levels = [row[0] for row in cursor.fetchall()]

        for level in levels:
            cursor = conn.execute(
                """
                SELECT v.german_word, v.spanish_translation, v.base_form
                FROM vocabulary v
                JOIN word_category_associations wca ON v.id = wca.vocabulary_id
                JOIN word_categories wc ON wca.category_id = wc.id
                WHERE wc.level = ?
                ORDER BY RANDOM()
                LIMIT ?
            """,
                (level, samples_per_level),
            )

            level_samples = []
            for _i, row in enumerate(cursor.fetchall(), 1):
                german = row[0]
                spanish = row[1]
                base_form = row[2]

                if base_form != german:
                    pass

                level_samples.append({"german": german, "spanish": spanish, "base_form": base_form})

            samples[level] = level_samples

        return samples

    except sqlite3.Error:
        return {}


def performance_testing(conn: sqlite3.Connection) -> dict[str, float]:
    """Test query performance for common database operations."""

    import time

    results = {}

    try:
        # Test 1: Simple vocabulary lookup
        start_time = time.time()
        cursor = conn.execute("SELECT * FROM vocabulary WHERE german_word = 'Haus'")
        cursor.fetchall()
        results["simple_lookup"] = time.time() - start_time

        # Test 2: Level-based query
        start_time = time.time()
        cursor = conn.execute("""
            SELECT v.german_word, v.spanish_translation
            FROM vocabulary v
            JOIN word_category_associations wca ON v.id = wca.vocabulary_id
            JOIN word_categories wc ON wca.category_id = wc.id
            WHERE wc.level = 'A1'
            LIMIT 100
        """)
        cursor.fetchall()
        results["level_query"] = time.time() - start_time

        # Test 3: Search query
        start_time = time.time()
        cursor = conn.execute("""
            SELECT v.german_word, v.spanish_translation
            FROM vocabulary v
            WHERE v.german_word LIKE 'haus%'
            LIMIT 50
        """)
        cursor.fetchall()
        results["search_query"] = time.time() - start_time

        # Test 4: Count query
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

    if (critical_issues == 0 and relationship_ok and total_entries > 5000) or (
        critical_issues <= 2 and relationship_ok and total_entries > 4000
    ):
        pass
    else:
        pass

    if performance_results:
        sum(performance_results.values()) / len(performance_results)

    if quality_stats.get("duplicates", 0) > 0:
        pass

    if quality_stats.get("german_special_pct", 0) < 5:
        pass

    if not relationship_ok:
        pass

    if any(time > 0.1 for time in performance_results.values()):
        pass

    if critical_issues == 0 and relationship_ok:
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
        performance_results = performance_testing(conn)

        # Compare with expected counts
        compare_with_expected_counts(counts)

        # Generate final report
        generate_final_report(counts, quality_stats, performance_results, relationship_ok)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
