"""
Create test video files and subtitles for testing
"""
from pathlib import Path

def create_test_videos():
    """Create test video files for the video endpoints"""
    videos_dir = Path("data/videos")
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some test video files (empty files for testing)
    test_videos = [
        ("episode1.mp4", "Episode 1: Introduction to German"),
        ("episode2.mp4", "Episode 2: Basic Greetings"),
        ("episode3.mp4", "Episode 3: Numbers and Counting"),
    ]
    
    for filename, title in test_videos:
        video_path = videos_dir / filename
        # Create empty file
        video_path.touch()
        print(f"Created test video: {video_path}")
        
        # Create corresponding subtitle file
        srt_path = video_path.with_suffix(".srt")
        srt_content = f"""1
00:00:00,000 --> 00:00:03,000
{title}

2
00:00:03,000 --> 00:00:06,000
Willkommen zum Deutschkurs!

3
00:00:06,000 --> 00:00:10,000
Heute lernen wir wichtige deutsche Wörter.
"""
        srt_path.write_text(srt_content, encoding="utf-8")
        print(f"Created subtitle: {srt_path}")
    
    print(f"\nCreated {len(test_videos)} test videos in {videos_dir}")
    return True

if __name__ == "__main__":
    create_test_videos()