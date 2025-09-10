#!/usr/bin/env python3
"""
Direct test of transcription endpoint to debug the 500 error
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_transcription_endpoint():
    """Test the transcription endpoint directly"""
    base_url = "http://localhost:8000"
    
    # First, register and login to get a token
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    print("Attempting to register user...")
    try:
        # Try to register first (ignore if user already exists)
        register_response = requests.post(f"{base_url}/auth/register", json=test_user)
        print(f"Register status: {register_response.status_code}")
        
        # Now login
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        
        print("Attempting to login...")
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login status: {login_response.status_code}")
        print(f"Login response: {login_response.text}")
        
        if login_response.status_code == 200:
            response_data = login_response.json()
            token = response_data.get("access_token") or response_data.get("token")
            print(f"Token obtained: {token[:20]}..." if token else "No token in response")
            
            # Now test transcription endpoint
            headers = {"Authorization": f"Bearer {token}"}
            transcription_data = {"video_path": "test_video.mp4"}
            
            print("\nTesting transcription endpoint...")
            transcription_response = requests.post(
                f"{base_url}/process/transcribe", 
                json=transcription_data,
                headers=headers
            )
            
            print(f"Transcription status: {transcription_response.status_code}")
            print(f"Transcription response: {transcription_response.text}")
            
            # If we get a task_id, check the task status
            if transcription_response.status_code == 200:
                task_data = transcription_response.json()
                task_id = task_data.get("task_id")
                if task_id:
                    print(f"\nTask started: {task_id}")
                    # Check task status
                    import time
                    time.sleep(2)
                    status_response = requests.get(
                        f"{base_url}/process/progress/{task_id}",
                        headers=headers
                    )
                    print(f"Task status: {status_response.status_code}")
                    print(f"Task response: {status_response.text}")
        else:
            print("Login failed, cannot test transcription endpoint")
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transcription_endpoint()