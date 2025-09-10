#!/usr/bin/env python3
"""
Debug script to test transcription endpoint directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import traceback
from fastapi.testclient import TestClient
from main import app
from core.dependencies import get_transcription_service
from api.routes.processing import run_transcription
from api.models.processing import ProcessingStatus

def test_transcription_service():
    """Test transcription service directly"""
    print("Testing transcription service...")
    try:
        service = get_transcription_service()
        print(f"Service: {service}")
        print(f"Service type: {type(service)}")
        return service is not None
    except Exception as e:
        print(f"Error getting transcription service: {e}")
        traceback.print_exc()
        return False

async def test_background_task():
    """Test the background task directly"""
    print("\nTesting background task...")
    try:
        task_progress = {}
        task_id = "test_task_123"
        video_path = "test_video.mp4"
        
        await run_transcription(video_path, task_id, task_progress)
        
        print(f"Task progress: {task_progress}")
        if task_id in task_progress:
            status = task_progress[task_id]
            print(f"Task status: {status.status}")
            print(f"Task message: {status.message}")
        
        return True
    except Exception as e:
        print(f"Error in background task: {e}")
        traceback.print_exc()
        return False

def test_endpoint():
    """Test the endpoint directly"""
    print("\nTesting endpoint...")
    try:
        client = TestClient(app)
        
        # First login to get auth token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code} - {login_response.text}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test transcription endpoint
        response = client.post(
            "/api/processing/transcribe",
            json={"video_path": "test_video.mp4", "language": "de"},
            headers=headers
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Transcription Debug Test ===")
    
    # Test 1: Transcription service
    service_ok = test_transcription_service()
    print(f"Transcription service test: {'PASS' if service_ok else 'FAIL'}")
    
    # Test 2: Background task
    task_ok = asyncio.run(test_background_task())
    print(f"Background task test: {'PASS' if task_ok else 'FAIL'}")
    
    # Test 3: Full endpoint
    endpoint_ok = test_endpoint()
    print(f"Endpoint test: {'PASS' if endpoint_ok else 'FAIL'}")
    
    print("\n=== Summary ===")
    print(f"Service: {'✓' if service_ok else '✗'}")
    print(f"Background Task: {'✓' if task_ok else '✗'}")
    print(f"Endpoint: {'✓' if endpoint_ok else '✗'}")