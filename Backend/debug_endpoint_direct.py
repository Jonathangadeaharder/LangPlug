#!/usr/bin/env python3
"""
Direct test of the transcription endpoint function
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from fastapi import BackgroundTasks
from api.routes.processing import transcribe_video
from api.models.processing import TranscribeRequest
from services.authservice.auth_service import AuthUser
from core.dependencies import get_task_progress_registry

async def test_endpoint_directly():
    """Test the endpoint function directly"""
    print("Testing transcription endpoint directly...")
    
    try:
        # Create mock objects
        request = TranscribeRequest(video_path="test_video.mp4")
        background_tasks = BackgroundTasks()
        
        # Create a mock user
        current_user = AuthUser(
            id=1,
            username="testuser",
            is_admin=False,
            is_active=True
        )
        
        # Get task progress registry
        task_progress = get_task_progress_registry()
        
        print(f"Request: {request}")
        print(f"User: {current_user}")
        print(f"Task progress registry: {task_progress}")
        
        # Call the endpoint function
        result = await transcribe_video(
            request=request,
            background_tasks=background_tasks,
            current_user=current_user,
            task_progress=task_progress
        )
        
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_endpoint_directly())
    print(f"Test {'PASSED' if success else 'FAILED'}")