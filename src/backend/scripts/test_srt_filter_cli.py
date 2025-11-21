#!/usr/bin/env python
"""
CLI tool to test SRT filtering functionality

Usage:
    python test_srt_filter_cli.py <path_to_srt_file>
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_srt_filter_cli.py <path_to_srt_file>")
        sys.exit(1)

    srt_file_path = sys.argv[1]

    print(f"[INFO] Testing SRT filter with file: {srt_file_path}")
    print(f"[INFO] Checking if file exists...")

    if not Path(srt_file_path).exists():
        print(f"[ERROR] File not found: {srt_file_path}")
        sys.exit(1)

    print(f"[INFO] File found, size: {Path(srt_file_path).stat().st_size} bytes")

    # Initialize processor
    print("[INFO] Initializing DirectSubtitleProcessor...")
    processor = DirectSubtitleProcessor()

    # Test with default settings
    user_id = "1"
    user_level = "B1"  # Intermediate level
    language = "de"  # German

    print(f"[INFO] Processing with:")
    print(f"  - User ID: {user_id}")
    print(f"  - User Level: {user_level}")
    print(f"  - Language: {language}")
    print()

    try:
        print("[INFO] Starting SRT file processing...")
        result = await processor.process_srt_file(
            srt_file_path=srt_file_path,
            user_id=user_id,
            user_level=user_level,
            language=language
        )

        print("\n[SUCCESS] Processing completed!")
        print(f"[RESULT] Output file: {result['output_file']}")
        print(f"[RESULT] Total subtitles: {result.get('total_subtitles', 'N/A')}")
        print(f"[RESULT] Filtered subtitles: {result.get('filtered_subtitles', 'N/A')}")
        print(f"[RESULT] Total words processed: {result.get('total_words_processed', 'N/A')}")
        print(f"[RESULT] Unique words: {result.get('unique_words', 'N/A')}")
        print(f"[RESULT] Unknown words: {result.get('unknown_words', 'N/A')}")

        # Show sample of filtered content if available
        if Path(result['output_file']).exists():
            print(f"\n[INFO] Reading first 500 chars of output...")
            with open(result['output_file'], 'r', encoding='utf-8') as f:
                sample = f.read(500)
                print(f"[SAMPLE] {sample}...")

    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        import traceback
        print(f"[TRACEBACK]")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
