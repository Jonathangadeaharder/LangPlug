#!/usr/bin/env python
"""Test SRT filtering on Episode 18"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor


async def main():
    # Use the Windows path directly (no command line args to avoid quoting issues)
    srt_file_path = r"C:\Users\jogah\Downloads\Episode 18 Staffel 1 von Desperate Housewives.m4a.srt"

    print("[INFO] Testing SRT filter with Episode 18")
    print(f"[INFO] File path: {srt_file_path}")
    print("[INFO] Checking if file exists...")

    if not Path(srt_file_path).exists():
        print(f"[ERROR] File not found: {srt_file_path}")
        sys.exit(1)

    file_size = Path(srt_file_path).stat().st_size
    print(f"[INFO] File found, size: {file_size:,} bytes")

    # Initialize processor
    print("[INFO] Initializing DirectSubtitleProcessor...")
    processor = DirectSubtitleProcessor()

    # Test with default settings
    user_id = "1"
    user_level = "B1"  # Intermediate level
    language = "de"  # German

    print("[INFO] Processing with:")
    print(f"  - User ID: {user_id}")
    print(f"  - User Level: {user_level}")
    print(f"  - Language: {language}")
    print()

    try:
        print("[INFO] Starting SRT file processing...")
        result = await processor.process_srt_file(
            srt_file_path=srt_file_path, user_id=user_id, user_level=user_level, language=language
        )

        print("\n[SUCCESS] Processing completed!")
        print(f"\n[RESULT] Keys in result: {list(result.keys())}")

        # Show statistics
        stats = result.get("statistics", {})
        print("\n[STATISTICS]")
        print(f"  - Total words processed: {stats.get('total_words_processed', 0):,}")
        print(f"  - Unique words: {stats.get('unique_words', 0):,}")
        print(f"  - Blocking words: {stats.get('blocking_words_count', 0):,}")
        print(f"  - Learning words: {stats.get('learning_words_count', 0):,}")
        print(f"  - Known words: {stats.get('known_words_count', 0):,}")

        # Show counts
        print("\n[SUBTITLES]")
        print(f"  - Filtered subtitles: {len(result.get('filtered_subtitles', [])):,}")
        print(f"  - Learning subtitles: {len(result.get('learning_subtitles', [])):,}")
        print(f"  - Empty subtitles: {len(result.get('empty_subtitles', [])):,}")

        # Show blocking words (first 20)
        blocking_words = result.get("blocking_words", [])
        if blocking_words:
            print(f"\n[BLOCKING WORDS] First 20 of {len(blocking_words)}:")
            for i, word in enumerate(blocking_words[:20], 1):
                # Handle both dict and Pydantic model
                if hasattr(word, "word"):
                    word_text = word.word
                    level = getattr(word, "difficulty_level", "N/A")
                elif hasattr(word, "lemma"):
                    word_text = word.lemma
                    level = getattr(word, "difficulty_level", "N/A")
                else:
                    word_text = str(word)
                    level = "N/A"
                print(f"  {i}. {word_text} (level: {level})")

        # Show sample of filtered subtitles
        filtered_subs = result.get("filtered_subtitles", [])
        if filtered_subs:
            print("\n[FILTERED SUBTITLES] First 10:")
            for i, sub in enumerate(filtered_subs[:10], 1):
                original = sub.original_text
                active = sub.active_text
                is_blocker = sub.is_blocker
                has_learning = sub.has_learning_content
                num_words = len(sub.words) if sub.words else 0

                status = "BLOCKER" if is_blocker else ("LEARNING" if has_learning else "ACTIVE")

                print(f"\n  [{i}] [{status}] ({num_words} words)")
                print(f"      Original: {original}")
                print(f"      Active:   {active}")

    except Exception as e:
        print("\n[ERROR] Processing failed!")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Message: {e}")
        print("\n[TRACEBACK]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 70)
    print("SRT Filter CLI Test - Episode 18")
    print("=" * 70)
    print()
    asyncio.run(main())
