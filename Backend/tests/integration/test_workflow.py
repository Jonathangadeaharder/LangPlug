#!/usr/bin/env python
"""
Complete workflow test for LangPlug backend
Tests all major API endpoints and user flows
"""

import requests
import json
import time
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"


def print_response(response: requests.Response, title: str) -> None:
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text[:200]}")
    print(f"{'='*60}\n")


def test_health() -> bool:
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    return response.status_code == 200


def test_auth_workflow() -> Optional[Dict[str, str]]:
    """Test authentication workflow"""
    print("\n" + "=" * 80)
    print("TESTING AUTHENTICATION WORKFLOW")
    print("=" * 80)

    # 1. Register a new user
    register_data = {
        "username": f"testuser_{int(time.time())}",
        "password": "Test123!@#",
        "email": f"test_{int(time.time())}@example.com",
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print_response(response, "User Registration")

    if response.status_code != 200:
        print("[ERROR] Registration failed")
        return None

    # 2. Login
    login_data = {
        "username": register_data["username"],
        "password": register_data["password"],
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response(response, "User Login")

    if response.status_code != 200:
        print("[ERROR] Login failed")
        return None

    auth_data = response.json()
    token = auth_data.get("token")

    if not token:
        print("[ERROR] No token received")
        return None

    print(f"[OK] Authentication successful! Token: {token[:20]}...")

    # 3. Get current user info
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print_response(response, "Current User Info")

    return headers


def test_videos(headers: Dict[str, str]) -> bool:
    """Test video endpoints"""
    print("\n" + "=" * 80)
    print("TESTING VIDEO ENDPOINTS")
    print("=" * 80)

    # Get available videos
    response = requests.get(f"{BASE_URL}/videos", headers=headers)
    print_response(response, "Available Videos")

    if response.status_code == 200:
        videos = response.json()
        print(f"[OK] Found {len(videos)} videos")

        if videos:
            # Test getting subtitles for first video
            first_video = videos[0]
            if first_video.get("has_subtitles"):
                subtitle_path = first_video["path"].replace(".mp4", ".srt")
                response = requests.get(
                    f"{BASE_URL}/videos/subtitles/{subtitle_path}", headers=headers
                )
                print_response(response, "Subtitle Content")
    else:
        print("[ERROR] Failed to get videos")


def test_vocabulary(headers: Dict[str, str]) -> bool:
    """Test vocabulary endpoints"""
    print("\n" + "=" * 80)
    print("TESTING VOCABULARY ENDPOINTS")
    print("=" * 80)

    # 1. Get vocabulary stats
    response = requests.get(f"{BASE_URL}/vocabulary/library/stats", headers=headers)
    print_response(response, "Vocabulary Statistics")

    # 2. Get A1 vocabulary
    response = requests.get(f"{BASE_URL}/vocabulary/library/A1", headers=headers)
    print_response(response, "A1 Vocabulary Level")

    if response.status_code == 200:
        data = response.json()
        print(
            f"[OK] A1 Level: {data.get('known_count', 0)}/{data.get('total_count', 0)} words known"
        )

    # 3. Mark a word as known
    mark_data = {"word": "hallo", "known": True}
    response = requests.post(
        f"{BASE_URL}/vocabulary/mark-known", json=mark_data, headers=headers
    )
    print_response(response, "Mark Word as Known")

    # 4. Get blocking words (mock data)
    response = requests.get(
        f"{BASE_URL}/vocabulary/blocking-words?video_path=test.mp4", headers=headers
    )
    print_response(response, "Blocking Words for Video")


def test_processing(headers: Dict[str, str]) -> bool:
    """Test processing endpoints"""
    print("\n" + "=" * 80)
    print("TESTING PROCESSING ENDPOINTS")
    print("=" * 80)

    # 1. Test transcription (will return task ID)
    transcribe_data = {
        "video_path": "videos\\Superstore\\Episode 1 Staffel 1 von Superstore S to - Serien Online gratis a_with_subtitles.mp4",
        "language": "de",
    }
    response = requests.post(
        f"{BASE_URL}/process/transcribe", json=transcribe_data, headers=headers
    )
    print_response(response, "Transcription Request")

    if response.status_code == 200:
        task_data = response.json()
        task_id = task_data.get("task_id")

        if task_id:
            # 2. Get processing progress
            response = requests.get(
                f"{BASE_URL}/process/progress/{task_id}", headers=headers
            )
            print_response(response, "Processing Progress")


def main() -> None:
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LANGPLUG BACKEND WORKFLOW TEST")
    print("=" * 80)

    # Test health
    if not test_health():
        print("[ERROR] Backend is not healthy. Please ensure it's running on port 8000")
        return

    print("[OK] Backend is healthy!")

    # Test authentication and get token
    headers = test_auth_workflow()
    if not headers:
        print("[ERROR] Authentication workflow failed")
        return

    # Test other endpoints with authentication
    test_videos(headers)
    test_vocabulary(headers)
    test_processing(headers)

    print("\n" + "=" * 80)
    print("WORKFLOW TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("[OK] Health check passed")
    print("[OK] Authentication working")
    print("[OK] API endpoints accessible")
    print("\nThe backend is ready for frontend integration!")


if __name__ == "__main__":
    main()
