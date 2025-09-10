#!/usr/bin/env python3
"""
Quick test to verify SRT generation is working with the updated code
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_srt_format():
    """Test that the SRT formatting function works correctly"""
    
    print("=" * 60)
    print("SRT FORMAT VERIFICATION TEST")
    print("=" * 60)
    
    # Import the format function from processing.py
    from api.routes.processing import _format_srt_timestamp
    
    print("\n1. Testing timestamp formatting...")
    
    test_cases = [
        (0.0, "00:00:00,000"),
        (1.5, "00:00:01,500"),
        (65.123, "00:01:05,123"),
        (3665.456, "01:01:05,456"),
        (7325.999, "02:02:05,999"),
    ]
    
    all_passed = True
    for seconds, expected in test_cases:
        result = _format_srt_timestamp(seconds)
        passed = result == expected
        all_passed = all_passed and passed
        status = "[OK]" if passed else "[FAIL]"
        print(f"   {status} {seconds:8.3f}s -> {result} (expected: {expected})")
    
    if not all_passed:
        print("\n[ERROR] Some timestamp formatting tests failed!")
        return False
    
    print("\n[OK] All timestamp formatting tests passed!")
    
    print("\n2. Creating mock transcription result...")
    
    # Create a mock transcription result to test SRT generation
    from services.transcriptionservice.interface import TranscriptionResult, TranscriptionSegment
    
    segments = [
        TranscriptionSegment(
            start_time=0.0,
            end_time=2.5,
            text="Willkommen bei Superstore.",
            metadata={}
        ),
        TranscriptionSegment(
            start_time=2.5,
            end_time=5.0,
            text="Hier ist alles möglich!",
            metadata={}
        ),
        TranscriptionSegment(
            start_time=5.0,
            end_time=8.2,
            text="Wir haben die besten Preise in der Stadt.",
            metadata={}
        ),
    ]
    
    result = TranscriptionResult(
        full_text=" ".join(seg.text for seg in segments),
        segments=segments,
        language="de",
        duration=8.2,
        metadata={}
    )
    
    print(f"[OK] Created mock result with {len(segments)} segments")
    
    print("\n3. Generating SRT content...")
    
    # Generate SRT content using the same logic as in processing.py
    srt_content = []
    for i, segment in enumerate(result.segments, 1):
        start_time = _format_srt_timestamp(segment.start_time)
        end_time = _format_srt_timestamp(segment.end_time)
        
        srt_content.append(f"{i}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(segment.text)
        srt_content.append("")  # Empty line between entries
    
    srt_text = "\n".join(srt_content)
    
    print("[OK] SRT content generated")
    
    print("\n4. Generated SRT content:")
    print("-" * 60)
    print(srt_text)
    print("-" * 60)
    
    # Verify the format
    lines = srt_text.split("\n")
    expected_lines = [
        "1",
        "00:00:00,000 --> 00:00:02,500",
        "Willkommen bei Superstore.",
        "",
        "2",
        "00:00:02,500 --> 00:00:05,000",
        "Hier ist alles möglich!",
        "",
        "3",
        "00:00:05,000 --> 00:00:08,200",
        "Wir haben die besten Preise in der Stadt.",
        "",
    ]
    
    if lines == expected_lines:
        print("\n[OK] SRT format is correct!")
        return True
    else:
        print("\n[ERROR] SRT format doesn't match expected output")
        print("Expected:")
        for line in expected_lines:
            print(f"  '{line}'")
        print("Got:")
        for line in lines:
            print(f"  '{line}'")
        return False


if __name__ == "__main__":
    try:
        success = test_srt_format()
        
        print("\n" + "=" * 60)
        if success:
            print("TEST PASSED: SRT formatting is working correctly!")
            print("\nThe system is now ready to generate real SRT files")
            print("from Whisper transcription results.")
        else:
            print("TEST FAILED: Check the errors above")
        print("=" * 60)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)