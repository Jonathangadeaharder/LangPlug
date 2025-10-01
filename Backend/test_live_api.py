"""Test the live API to see what's actually being returned"""
import requests
import json

# Get auth token first
print("=" * 80)
print("TESTING LIVE API")
print("=" * 80)

# Login to get token
print("\n1. Logging in...")
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "test", "password": "test123"}
)

if login_response.status_code != 200:
    print(f"[POOR] Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"[GOOD] Got auth token: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}"}

# Start chunk processing
print("\n2. Starting chunk processing...")
chunk_request = {
    "video_path": "test_video.mp4",  # Use a test video path
    "start_time": 0,
    "end_time": 60
}

chunk_response = requests.post(
    "http://localhost:8000/api/process/chunk",
    json=chunk_request,
    headers=headers
)

if chunk_response.status_code != 200:
    print(f"[WARN] Chunk processing request failed: {chunk_response.status_code}")
    print(chunk_response.text)
    print("\nThis is expected if test_video.mp4 doesn't exist.")
    print("The important thing is to check if the backend is running and using new code.")
    exit(0)

task_id = chunk_response.json()["task_id"]
print(f"[GOOD] Task started: {task_id}")

# Poll for results
print("\n3. Polling for results...")
import time
for i in range(10):
    time.sleep(2)
    progress_response = requests.get(
        f"http://localhost:8000/api/process/progress/{task_id}",
        headers=headers
    )

    if progress_response.status_code != 200:
        print(f"[POOR] Progress check failed: {progress_response.status_code}")
        continue

    progress = progress_response.json()
    print(f"  Status: {progress['status']}, Progress: {progress['progress']}%")

    if progress['status'] == 'completed':
        print("\n4. Checking vocabulary lemmas...")
        vocabulary = progress.get('vocabulary', [])
        print(f"Found {len(vocabulary)} words")

        for word in vocabulary[:5]:  # Show first 5
            print(f"\n  Word: {word.get('word')}")
            print(f"  Lemma: {word.get('lemma')}")
            print(f"  Level: {word.get('difficulty_level')}")

            if word.get('word') == 'trauriger':
                if word.get('lemma') == 'traurig':
                    print("  [GOOD] Lemma is CORRECT!")
                else:
                    print(f"  [POOR] Lemma is WRONG! Expected 'traurig', got '{word.get('lemma')}'")
        break

    if progress['status'] == 'error':
        print(f"[POOR] Processing failed: {progress.get('message')}")
        break

print("\n" + "=" * 80)
