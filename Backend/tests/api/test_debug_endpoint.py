#!/usr/bin/env python3
"""Test the debug endpoint directly"""

import requests
from datetime import datetime

# Test data
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "level": "INFO",
    "category": "Test",
    "message": "Test log from direct API call",
    "data": {"test": True},
    "url": "http://localhost:3000/test",
    "userAgent": "TestScript/1.0"
}

try:
    # Test the endpoint
    response = requests.post(
        "http://localhost:8000/debug/frontend-logs",
        json=log_entry,
        headers={
            "Content-Type": "application/json",
            "Origin": "http://localhost:3000"
        },
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("[OK] Debug endpoint is working!")
    else:
        print(f"[ERROR] Debug endpoint returned {response.status_code}")
        
except requests.exceptions.ConnectionError as e:
    print("[ERROR] Cannot connect to backend at localhost:8000")
    print(f"Error: {e}")
except requests.exceptions.Timeout as e:
    print("[ERROR] Request timed out")
    print(f"Error: {e}")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")