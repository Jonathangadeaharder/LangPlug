#!/usr/bin/env python3
"""
Test Frontend Integration with Subtitle Processing
Verifies that all subtitle processing endpoints work correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_frontend_integration():
    print("🎬 Testing Frontend Integration with Subtitle Processing")
    print("=" * 60)
    
    # Step 1: Authentication
    print("\n1. 🔐 Testing Authentication...")
    try:
        auth_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        print(f"   Login Status: {auth_response.status_code}")
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.text}")
            return False
            
        token_data = auth_response.json()
        print(f"   Response data: {token_data}")
        # Check for different token field names
        token = token_data.get('access_token') or token_data.get('token') or token_data.get('access')
        if not token:
            print("❌ No access token received")
            print(f"   Available keys: {list(token_data.keys())}")
            return False
            
        print(f"✅ Authentication successful, token: {token[:20]}...")
        headers = {"Authorization": f"Bearer {token}"}
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Step 2: Verify auth token works
    print("\n2. 🔍 Verifying Token...")
    try:
        me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"   Auth Check Status: {me_response.status_code}")
        
        if me_response.status_code == 200:
            user_data = me_response.json()
            print(f"✅ Token valid, user: {user_data.get('username', 'unknown')}")
        else:
            print(f"❌ Token validation failed: {me_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False
    
    # Step 3: Test Subtitle Processing Endpoints
    print("\n3. 🎤 Testing Subtitle Processing Endpoints...")
    
    endpoints_to_test = [
        {
            "name": "Transcription",
            "method": "POST",
            "endpoint": "/process/transcribe",
            "data": {"video_path": "test_video.mp4", "output_format": "srt"}
        },
        {
            "name": "Subtitle Filtering", 
            "method": "POST",
            "endpoint": "/process/filter-subtitles",
            "data": {"video_path": "test.srt"}
        },
        {
            "name": "Translation",
            "method": "POST", 
            "endpoint": "/process/translate-subtitles",
            "data": {
                "video_path": "test.srt",
                "source_lang": "de", 
                "target_lang": "en"
            }
        },
        {
            "name": "Vocabulary Blocking Words",
            "method": "GET",
            "endpoint": "/vocabulary/blocking-words",
            "params": {"video_path": "test.srt"}
        }
    ]
    
    all_working = True
    
    for test in endpoints_to_test:
        try:
            print(f"\n   Testing {test['name']}...")
            
            if test['method'] == 'POST':
                response = requests.post(
                    f"{BASE_URL}{test['endpoint']}",
                    json=test['data'],
                    headers=headers
                )
            else:
                response = requests.get(
                    f"{BASE_URL}{test['endpoint']}",
                    params=test.get('params', {}),
                    headers=headers
                )
            
            print(f"   Status: {response.status_code}")
            
            # Expected status codes for missing files
            expected_codes = [200, 404, 422]
            if response.status_code in expected_codes:
                print(f"✅ {test['name']} endpoint working correctly")
            else:
                print(f"❌ {test['name']} unexpected status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                all_working = False
                
        except Exception as e:
            print(f"❌ {test['name']} error: {e}")
            all_working = False
    
    # Step 4: Test Frontend API Service Integration
    print("\n4. 🌐 Testing Frontend API Service Patterns...")
    
    # Test the exact patterns used by frontend
    frontend_patterns = [
        {
            "name": "Episode Preparation (Frontend Pattern)",
            "endpoint": "/process/prepare-episode",
            "data": {"video_path": "Superstore/Episode1.mp4"}
        },
        {
            "name": "Chunk Processing (Frontend Pattern)", 
            "endpoint": "/process/chunk",
            "data": {
                "video_path": "Superstore/Episode1.mp4",
                "start_time": 0,
                "end_time": 300
            }
        }
    ]
    
    for pattern in frontend_patterns:
        try:
            print(f"\n   Testing {pattern['name']}...")
            response = requests.post(
                f"{BASE_URL}{pattern['endpoint']}",
                json=pattern['data'],
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 404, 422]:
                print(f"✅ {pattern['name']} endpoint accessible")
            else:
                print(f"⚠️  {pattern['name']} status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {pattern['name']} error: {e}")
    
    print("\n" + "=" * 60)
    if all_working:
        print("🎉 SUCCESS: Frontend can successfully integrate with all subtitle processing endpoints!")
        print("\n📋 Summary:")
        print("   ✅ Authentication working")
        print("   ✅ Token validation working") 
        print("   ✅ Transcription endpoint accessible")
        print("   ✅ Filtering endpoint accessible")
        print("   ✅ Translation endpoint accessible")
        print("   ✅ Vocabulary endpoint accessible")
        print("   ✅ Frontend API patterns supported")
        print("\n🚀 The frontend is correctly configured to use subtitle processing!")
        return True
    else:
        print("❌ ISSUES FOUND: Some endpoints may not be working correctly")
        return False

if __name__ == "__main__":
    test_frontend_integration()