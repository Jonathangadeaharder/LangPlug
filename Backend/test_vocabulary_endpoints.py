#!/usr/bin/env python3
"""
Test vocabulary endpoints with proper authentication
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_vocabulary_endpoints():
    """Test vocabulary endpoints with proper authentication"""
    print("🔤 Testing Vocabulary Endpoints with Authentication")
    print("=" * 60)
    
    # Step 1: Authenticate
    print("\n1. 🔐 Authenticating...")
    try:
        auth_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        print(f"   Login Status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            token = auth_data.get('token')
            if token:
                print(f"✅ Authentication successful! Token: {token[:20]}...")
                headers = {"Authorization": f"Bearer {token}"}
            else:
                print("❌ No token received")
                return False
        else:
            print(f"❌ Authentication failed: {auth_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Step 2: Test vocabulary endpoints
    print("\n2. 📚 Testing Vocabulary Endpoints...")
    
    endpoints_to_test = [
        {
            "name": "Vocabulary Stats",
            "method": "GET",
            "url": f"{BASE_URL}/vocabulary/library/stats",
            "expected_keys": ["levels", "total_words", "total_known"]
        },
        {
            "name": "Vocabulary Preload",
            "method": "POST",
            "url": f"{BASE_URL}/vocabulary/preload",
            "expected_keys": ["success", "message"]
        },
        {
            "name": "Blocking Words",
            "method": "GET",
            "url": f"{BASE_URL}/vocabulary/blocking-words",
            "params": {"video_path": "test_video.mp4", "segment_start": 0, "segment_duration": 300},
            "expected_keys": ["blocking_words"]
        },
        {
            "name": "Mark Word as Known",
            "method": "POST",
            "url": f"{BASE_URL}/vocabulary/mark-known",
            "json": {"word": "test", "known": True},
            "expected_keys": ["success"]
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n   Testing {endpoint['name']}...")
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'],
                    headers=headers,
                    params=endpoint.get('params', {})
                )
            elif endpoint['method'] == 'POST':
                response = requests.post(
                    endpoint['url'],
                    headers=headers,
                    json=endpoint.get('json', {})
                )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response keys: {list(data.keys())}")
                    
                    # Check if expected keys are present
                    expected_keys = endpoint.get('expected_keys', [])
                    missing_keys = [key for key in expected_keys if key not in data]
                    
                    if missing_keys:
                        print(f"   ⚠️  Missing expected keys: {missing_keys}")
                        results.append(f"{endpoint['name']}: PARTIAL (missing keys: {missing_keys})")
                    else:
                        print(f"   ✅ {endpoint['name']}: SUCCESS")
                        results.append(f"{endpoint['name']}: SUCCESS")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON response: {response.text[:100]}...")
                    results.append(f"{endpoint['name']}: SUCCESS (non-JSON)")
                    
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed: {response.text}")
                results.append(f"{endpoint['name']}: AUTH_FAILED")
            elif response.status_code == 404:
                print(f"   ⚠️  Endpoint not found: {response.text}")
                results.append(f"{endpoint['name']}: NOT_FOUND")
            else:
                print(f"   ❌ Unexpected status: {response.text}")
                results.append(f"{endpoint['name']}: ERROR ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            results.append(f"{endpoint['name']}: EXCEPTION")
    
    # Step 3: Summary
    print("\n" + "=" * 60)
    print("📊 VOCABULARY ENDPOINTS TEST SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for result in results if "SUCCESS" in result)
    total_count = len(results)
    
    for result in results:
        status_icon = "✅" if "SUCCESS" in result else "❌" if "ERROR" in result or "EXCEPTION" in result or "AUTH_FAILED" in result else "⚠️"
        print(f"   {status_icon} {result}")
    
    print(f"\n📈 Results: {success_count}/{total_count} endpoints working correctly")
    
    if success_count == total_count:
        print("🎉 ALL VOCABULARY ENDPOINTS ARE WORKING!")
        return True
    elif success_count > 0:
        print("⚠️  SOME VOCABULARY ENDPOINTS ARE WORKING")
        return True
    else:
        print("❌ NO VOCABULARY ENDPOINTS ARE WORKING")
        return False

if __name__ == "__main__":
    test_vocabulary_endpoints()