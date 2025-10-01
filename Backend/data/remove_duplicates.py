#!/usr/bin/env python3
"""
Remove duplicate entries from vocabulary files while preserving order.
"""

import csv


def remove_duplicates_from_file(filepath: str) -> tuple[int, int]:
    """Remove duplicates from a vocabulary file, returns (original_count, new_count)."""

    # Read all entries
    entries = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            german = row.get("Deutsch_grundform", "").strip()
            spanish = row.get("spanisch_grundform", "").strip()
            if german and spanish:
                entries.append((german, spanish))

    original_count = len(entries)

    # Remove duplicates while preserving order
    seen = set()
    unique_entries = []

    for german, spanish in entries:
        # Use German word as primary key for deduplication
        if german not in seen:
            seen.add(german)
            unique_entries.append((german, spanish))
        else:
            pass

    # Write back the deduplicated entries
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Deutsch_grundform", "spanisch_grundform"])
        for german, spanish in unique_entries:
            writer.writerow([german, spanish])

    return original_count, len(unique_entries)


def main():
    pass


def remove_internal_duplicates(filename):
    """Remove duplicate entries within a single file, keeping the first occurrence."""
    if not os.path.exists(filename):
        return

    with open(filename, encoding="utf-8") as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    if len(all_rows) < 2:
        return

    header = all_rows[0]
    data_rows = all_rows[1:]

    # Track seen German words (first column)
    seen_words = set()
    unique_rows = []
    duplicates_removed = 0

    for row in data_rows:
        if len(row) >= 2:
            german_word = row[0].strip()
            if german_word not in seen_words:
                seen_words.add(german_word)
                unique_rows.append(row)
            else:
                duplicates_removed += 1

    # Write back to file
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(unique_rows)

    return duplicates_removed


def remove_cross_level_duplicates():
    """Remove words that appear in multiple levels, keeping them in the lowest level only."""
    # Load all files
    all_data = {}
    word_locations = {}  # word -> [(level, row_index, row_data), ...]

    for level, filename in files.items():
        if not os.path.exists(filename):
            continue

        with open(filename, encoding="utf-8") as f:
            reader = csv.reader(f)
            all_rows = list(reader)

        header = all_rows[0] if all_rows else ["Deutsch_grundform", "spanisch_grundform"]
        data_rows = all_rows[1:] if len(all_rows) > 1 else []
        all_data[level] = {"header": header, "rows": data_rows}

        # Track word locations
        for i, row in enumerate(data_rows):
            if len(row) >= 2:
                german_word = row[0].strip()
                if german_word not in word_locations:
                    word_locations[german_word] = []
                word_locations[german_word].append((level, i, row))

    # Find cross-level duplicates
    level_hierarchy = ["A1", "A2", "B1", "B2", "C1"]
    cross_duplicates = {}
    total_removed = 0

    for _word, locations in word_locations.items():
        if len(locations) > 1:
            # Sort by level hierarchy
            locations.sort(key=lambda x: level_hierarchy.index(x[0]))

            # Keep in lowest level, mark others for removal
            locations[0][0]
            for level, row_idx, _row_data in locations[1:]:
                if level not in cross_duplicates:
                    cross_duplicates[level] = set()
                cross_duplicates[level].add(row_idx)
                total_removed += 1

    # Remove marked rows
    for level in all_data:
        if level in cross_duplicates:
            indices_to_remove = cross_duplicates[level]
            new_rows = [row for i, row in enumerate(all_data[level]["rows"]) if i not in indices_to_remove]
            all_data[level]["rows"] = new_rows

    # Write all files back
    for level, data in all_data.items():
        filename = files[level]
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(data["header"])
            writer.writerows(data["rows"])

    return total_removed


# Main execution
total_internal = 0
for _level, filename in files.items():
    removed = remove_internal_duplicates(filename)
    if removed:
        total_internal += removed

total_cross = remove_cross_level_duplicates()
