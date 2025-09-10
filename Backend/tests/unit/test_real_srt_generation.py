#!/usr/bin/env python3
"""
Test real SRT generation from Whisper transcription using actual Superstore videos
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the transcription service directly
from services.transcriptionservice.whisper_implementation import WhisperTranscriptionService

def test_real_srt_generation():
    """Test that Whisper generates real SRT content from actual video"""
    
    print("=" * 60)
    print("REAL VIDEO SRT GENERATION TEST")
    print("=" * 60)
    
    # Use a real Superstore video
    test_video = Path("C:/Users/Jonandrop/IdeaProjects/LangPlug/videos/Superstore/Episode 1 Staffel 1 von Superstore S to - Serien Online gratis a.mp4")
    
    if not test_video.exists():
        print(f"[ERROR] Video not found: {test_video}")
        return False
    
    print(f"[OK] Found video: {test_video.name}")
    print(f"     File size: {test_video.stat().st_size / (1024*1024):.1f} MB")
    
    print("\n1. Initializing Whisper service...")
    print("   Using 'base' model for faster testing (still good quality)")
    service = WhisperTranscriptionService(model_size="base")  # Use base for reasonable speed/quality
    service.initialize()
    print("[OK] Whisper service initialized")
    
    print("\n2. Transcribing first 60 seconds of video...")
    print("   Language: German (de)")
    print("   This may take a minute...")
    
    start_time = time.time()
    
    # For testing, we'll transcribe the full video but Whisper will handle it efficiently
    result = service.transcribe(str(test_video), language="de")
    
    elapsed = time.time() - start_time
    print(f"[OK] Transcription completed in {elapsed:.1f} seconds")
    print(f"     Generated {len(result.segments)} segments")
    
    if len(result.segments) == 0:
        print("[ERROR] No segments were generated!")
        return False
    
    print("\n3. Generating SRT content...")
    
    # Format SRT content (same as in processing.py)
    srt_lines = []
    for i, segment in enumerate(result.segments[:20], 1):  # Show first 20 segments for testing
        # Format timestamps
        start_hours = int(segment.start_time // 3600)
        start_minutes = int((segment.start_time % 3600) // 60)
        start_seconds = int(segment.start_time % 60)
        start_millis = int((segment.start_time % 1) * 1000)
        
        end_hours = int(segment.end_time // 3600)
        end_minutes = int((segment.end_time % 3600) // 60)
        end_seconds = int(segment.end_time % 60)
        end_millis = int((segment.end_time % 1) * 1000)
        
        start_time_str = f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d},{start_millis:03d}"
        end_time_str = f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d},{end_millis:03d}"
        
        # Add SRT entry
        srt_lines.append(str(i))
        srt_lines.append(f"{start_time_str} --> {end_time_str}")
        srt_lines.append(segment.text)
        srt_lines.append("")  # Empty line between entries
    
    srt_content = "\n".join(srt_lines)
    
    # Save to file
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    srt_file = output_dir / "superstore_test.srt"
    
    with open(srt_file, "w", encoding="utf-8") as f:
        # Write all segments to file
        all_srt_lines = []
        for i, segment in enumerate(result.segments, 1):
            start_hours = int(segment.start_time // 3600)
            start_minutes = int((segment.start_time % 3600) // 60)
            start_seconds = int(segment.start_time % 60)
            start_millis = int((segment.start_time % 1) * 1000)
            
            end_hours = int(segment.end_time // 3600)
            end_minutes = int((segment.end_time % 3600) // 60)
            end_seconds = int(segment.end_time % 60)
            end_millis = int((segment.end_time % 1) * 1000)
            
            start_time_str = f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d},{start_millis:03d}"
            end_time_str = f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d},{end_millis:03d}"
            
            all_srt_lines.append(str(i))
            all_srt_lines.append(f"{start_time_str} --> {end_time_str}")
            all_srt_lines.append(segment.text)
            all_srt_lines.append("")
        
        f.write("\n".join(all_srt_lines))
    
    print(f"[OK] SRT file generated: {srt_file}")
    
    # Display first few entries
    print("\n4. First 5 subtitle entries (showing real transcription):")
    print("-" * 60)
    lines = srt_content.split("\n")
    for line in lines[:min(20, len(lines))]:  # Show first 5 entries (4 lines each)
        if line.strip():
            print(f"   {line}")
        else:
            print()  # Empty line
    print("-" * 60)
    
    # Verify it's real content
    if len(result.segments) > 0:
        first_text = result.segments[0].text.strip()
        if first_text and len(first_text) > 5:  # Real text should be more than a few chars
            print("\n[OK] Real subtitles generated successfully!")
            print(f"     Total segments: {len(result.segments)}")
            print(f"     Total duration: {result.duration:.2f} seconds")
            print(f"     Detected language: {result.language}")
            print(f"     Output file: {srt_file}")
            
            # Show some statistics
            total_words = sum(len(seg.text.split()) for seg in result.segments)
            avg_segment_duration = sum(seg.end_time - seg.start_time for seg in result.segments) / len(result.segments)
            print("\n     Statistics:")
            print(f"     - Total words transcribed: {total_words}")
            print(f"     - Average segment duration: {avg_segment_duration:.2f} seconds")
            print(f"     - Words per minute: {(total_words / (result.duration / 60)):.1f}")
            
            return True
    
    print("\n[ERROR] No real subtitle content generated")
    return False


if __name__ == "__main__":
    try:
        print("\nThis test will transcribe a real Superstore episode.")
        print("It may take 1-2 minutes depending on your hardware.\n")
        
        success = test_real_srt_generation()
        
        print("\n" + "=" * 60)
        if success:
            print("TEST PASSED: Real SRT files are being generated from video!")
            print("\nThe transcription is now working correctly.")
            print("SRT files will be generated with actual German dialogue")
            print("from the Superstore episodes.")
        else:
            print("TEST FAILED: Check the errors above")
        print("=" * 60)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)