#!/usr/bin/env python3
"""
Debug script to test transcription service creation and identify the exact error
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import traceback
from core.dependencies import get_transcription_service
from services.transcriptionservice.factory import TranscriptionServiceFactory
from core.config import settings

def debug_transcription_service():
    """Debug transcription service creation step by step"""
    print("=== Debugging Transcription Service Creation ===")
    
    # Step 1: Check settings
    print(f"\n1. Settings:")
    print(f"   transcription_service: {settings.transcription_service}")
    
    # Step 2: Test factory directly
    print(f"\n2. Testing TranscriptionServiceFactory directly:")
    try:
        service = TranscriptionServiceFactory.create_service(settings.transcription_service)
        print(f"   Factory created service: {service}")
        print(f"   Service type: {type(service)}")
        
        # Try to initialize it
        print(f"\n3. Testing service initialization:")
        service.initialize()
        print(f"   Service initialized successfully")
        print(f"   Is initialized: {service.is_initialized}")
        
    except Exception as e:
        print(f"   Factory error: {e}")
        print(f"   Error type: {type(e)}")
        print(f"   Error str: '{str(e)}'")
        print(f"   Error repr: {repr(e)}")
        traceback.print_exc()
    
    # Step 3: Test dependencies function
    print(f"\n4. Testing get_transcription_service() from dependencies:")
    try:
        service = get_transcription_service()
        print(f"   Dependencies returned: {service}")
        if service is None:
            print(f"   Service is None - this explains the empty error!")
    except Exception as e:
        print(f"   Dependencies error: {e}")
        print(f"   Error type: {type(e)}")
        print(f"   Error str: '{str(e)}'")
        print(f"   Error repr: {repr(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_transcription_service()