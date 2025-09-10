#!/usr/bin/env python3
"""
Simple test to verify SRT generation from Whisper transcription
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the transcription service directly
from services.transcriptionservice.whisper_implementation import WhisperTranscriptionService

def test_srt_generation():
    """Test that Whisper generates real SRT content"""
    
    print("=" * 60)
    print("DIRECT SRT GENERATION TEST")
    print("=" * 60)
    
    # Create a simple test audio file (or use existing)
    test_video = Path(__file__).parent / "data" / "videos" / "episode1.mp4"
    
    if not test_video.exists():
        print(f"[ERROR] Test video not found: {test_video}")
        print("Creating a test video with audio...")
        # We can't create a real video easily, so let's just test with what we have
        videos_dir = Path(__file__).parent / "data" / "videos"
        if videos_dir.exists():
            videos = list(videos_dir.glob("*.mp4"))
            if videos:
                test_video = videos[0]
                print(f"[OK] Using existing video: {test_video.name}")
            else:
                print("[ERROR] No videos found in videos directory")
                return False
        else:
            print("[ERROR] Videos directory does not exist")
            return False
    
    print("\n1. Initializing Whisper service...")
    service = WhisperTranscriptionService(model_size="tiny")  # Use tiny for faster testing
    service.initialize()
    print("[OK] Whisper service initialized")
    
    print(f"\n2. Transcribing {test_video.name}...")
    result = service.transcribe(str(test_video), language="de")
    print(f"[OK] Transcription completed with {len(result.segments)} segments")
    
    print("\n3. Generating SRT content...")
    
    # Format SRT content
    srt_lines = []
    for i, segment in enumerate(result.segments, 1):
        # Format timestamps
        start_hours = int(segment.start_time // 3600)
        start_minutes = int((segment.start_time % 3600) // 60)
        start_seconds = int(segment.start_time % 60)
        start_millis = int((segment.start_time % 1) * 1000)
        
        end_hours = int(segment.end_time // 3600)
        end_minutes = int((segment.end_time % 3600) // 60)
        end_seconds = int(segment.end_time % 60)
        end_millis = int((segment.end_time % 1) * 1000)
        
        start_time = f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d},{start_millis:03d}"
        end_time = f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d},{end_millis:03d}"
        
        # Add SRT entry
        srt_lines.append(str(i))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(segment.text)
        srt_lines.append("")  # Empty line between entries
    
    srt_content = "\n".join(srt_lines)
    
    # Save to file
    srt_file = test_video.with_suffix(".srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    print(f"[OK] SRT file generated: {srt_file}")
    
    # Display first few entries
    print("\n4. First few subtitle entries:")
    print("-" * 50)
    lines = srt_content.split("\n")
    for line in lines[:min(12, len(lines))]:
        print(f"   {line}")
    print("-" * 50)
    
    # Verify it's real content
    if len(result.segments) > 0 and result.segments[0].text.strip():
        print("\n[OK] Real subtitles generated successfully!")
        print(f"     Total segments: {len(result.segments)}")
        print(f"     Total duration: {result.duration:.2f} seconds")
        return True
    else:
        print("\n[ERROR] No real subtitle content generated")
        return False


if __name__ == "__main__":
    try:
        success = test_srt_generation()
        print("\n" + "=" * 60)
        if success:
            print("TEST PASSED: Real SRT files are being generated!")
        else:
            print("TEST FAILED: Check the errors above")
        print("=" * 60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)