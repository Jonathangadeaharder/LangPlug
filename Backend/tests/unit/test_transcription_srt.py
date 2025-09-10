#!/usr/bin/env python3
"""
Test script to verify real SRT generation from Whisper transcription
"""

import sys
import requests
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_transcription_with_srt():
    """Test that transcription generates real SRT files with actual subtitles"""
    
    base_url = "http://localhost:8000"
    
    # Step 1: Login
    print("1. Logging in...")
    login_response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return False
    
    # Check which field contains the token
    response_data = login_response.json()
    token = response_data.get("access_token") or response_data.get("token")
    if not token:
        print(f"No token found in response: {response_data}")
        return False
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Logged in successfully")
    
    # Step 2: Get list of videos
    print("\n2. Getting list of videos...")
    videos_response = requests.get(f"{base_url}/videos", headers=headers)
    
    if videos_response.status_code != 200:
        print(f"Failed to get videos: {videos_response.text}")
        return False
    
    videos = videos_response.json()
    if not videos:
        print("No videos found. Please add a test video to the videos directory.")
        return False
    
    # Debug: check the structure of the response
    print(f"   Videos response structure: {list(videos[0].keys()) if videos else 'empty'}")
    
    # Use the first video - check for different possible keys
    video = videos[0]
    video_file = video.get("filename") or video.get("name") or video.get("file") or video.get("path")
    if not video_file:
        print(f"[ERROR] Could not find video filename in response: {video}")
        return False
    print(f"[OK] Found video: {video_file}")
    
    # Step 3: Start transcription
    print(f"\n3. Starting transcription for {video_file}...")
    transcribe_response = requests.post(
        f"{base_url}/process/transcribe",
        headers=headers,
        json={"video_path": video_file}
    )
    
    if transcribe_response.status_code != 200:
        print(f"Failed to start transcription: {transcribe_response.text}")
        return False
    
    task_id = transcribe_response.json()["task_id"]
    print(f"[OK] Transcription started with task ID: {task_id}")
    
    # Step 4: Poll for completion
    print("\n4. Waiting for transcription to complete...")
    max_attempts = 60  # Wait up to 60 seconds
    for attempt in range(max_attempts):
        status_response = requests.get(
            f"{base_url}/process/progress/{task_id}",
            headers=headers
        )
        
        if status_response.status_code != 200:
            print(f"Failed to get status: {status_response.text}")
            return False
        
        status = status_response.json()
        print(f"   Status: {status['status']} - {status['current_step']} ({status['progress']:.0f}%)")
        
        if status["status"] == "completed":
            print("[OK] Transcription completed!")
            break
        elif status["status"] == "error":
            print(f"[ERROR] Transcription failed: {status['message']}")
            return False
        
        time.sleep(2)
    else:
        print("[ERROR] Transcription timed out")
        return False
    
    # Step 5: Check the generated SRT file
    print("\n5. Checking generated SRT file...")
    videos_dir = Path(__file__).parent / "videos"
    video_path = videos_dir / video_file
    srt_path = video_path.with_suffix(".srt")
    
    if not srt_path.exists():
        print(f"[ERROR] SRT file not found: {srt_path}")
        return False
    
    # Read and display first few subtitles
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()
    
    lines = srt_content.strip().split("\n")
    print(f"[OK] SRT file generated with {len(lines)} lines")
    
    # Show first 3 subtitle entries (12 lines)
    print("\n   First few subtitle entries:")
    print("   " + "-" * 50)
    for line in lines[:min(12, len(lines))]:
        print(f"   {line}")
    print("   " + "-" * 50)
    
    # Verify it's not the mock subtitle
    if "[Transcription completed]" in srt_content and len(lines) < 10:
        print("\n[ERROR] WARNING: Still using mock subtitles!")
        return False
    
    print("\n[OK] Real subtitles generated successfully!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TRANSCRIPTION SRT GENERATION TEST")
    print("=" * 60)
    
    success = test_transcription_with_srt()
    
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED: Real SRT files are being generated!")
    else:
        print("TEST FAILED: Check the errors above")
    print("=" * 60)
    
    sys.exit(0 if success else 1)