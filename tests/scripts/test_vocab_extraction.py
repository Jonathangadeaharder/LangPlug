#!/usr/bin/env python3
"""Test vocabulary extraction from Malcolm Mittendrin SRT file"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))

async def test_vocab_extraction():
    from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
    
    # Path to SRT file (absolute)
    srt_file = str(Path(__file__).parent / "src" / "videos" / "Malcolm Mittendrin" / "Episode 1 Staffel 1 von Malcolm Mittendrin S to - Serien Online .srt")
    
    # Create processor
    processor = DirectSubtitleProcessor()
    
    # Process SRT file
    print(f"Processing: {srt_file}")
    result = await processor.process_srt_file(
        srt_file_path=srt_file,
        user_id=3,
        user_level="A1",
        language="de"
    )
    
    # Print results
    print(f"\n=== RESULTS ===")
    print(f"Blocking words: {len(result.get('blocking_words', []))}")
    print(f"Learning subtitles: {len(result.get('learning_subtitles', []))}")
    print(f"Empty subtitles: {len(result.get('empty_subtitles', []))}")
    
    if result.get('statistics'):
        print(f"\n=== STATISTICS ===")
        for key, value in result['statistics'].items():
            print(f"  {key}: {value}")
    
    if result.get('blocking_words'):
        print(f"\n=== SAMPLE BLOCKING WORDS ===")
        for word in result['blocking_words'][:5]:
            word_text = word.get('word', word.get('text', 'unknown'))
            difficulty = word.get('difficulty_level', word.get('metadata', {}).get('difficulty_level', 'N/A'))
            print(f"  - {word_text} (level: {difficulty})")
    
    if result.get('learning_subtitles'):
        print(f"\n=== SAMPLE LEARNING SUBTITLE ===")
        subtitle = result['learning_subtitles'][0]
        print(f"  Text: {subtitle.get('text', 'N/A')}")
        if 'active_words' in subtitle:
            print(f"  Active words: {len(subtitle['active_words'])}")
            for word in subtitle['active_words'][:3]:
                word_text = word.get('word', word.get('text', 'unknown'))
                print(f"    - {word_text}")

if __name__ == "__main__":
    asyncio.run(test_vocab_extraction())
