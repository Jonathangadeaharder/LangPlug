#!/usr/bin/env python3
"""
Test minimal POST endpoints to isolate timeout issue
"""
import requests
import time

def test_minimal_post():
    """Test minimal POST endpoint"""
    
    url = "http://localhost:8000/debug/test-minimal"
    
    print(f"Testing minimal POST endpoint: {url}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url, 
            json={},
            timeout=15  # 15 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"[OK] Request completed in {elapsed:.3f} seconds")
        print(f"[OK] Status code: {response.status_code}")
        print(f"[OK] Response: {response.text}")
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] REQUEST TIMED OUT after {elapsed:.3f} seconds")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request failed after {elapsed:.3f} seconds: {str(e)}")

def test_with_data_post():
    """Test POST endpoint with data"""
    
    url = "http://localhost:8000/debug/test-with-data"
    data = {"test": "value", "number": 123}
    
    print(f"\nTesting POST endpoint with data: {url}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url, 
            json=data,
            timeout=15  # 15 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"[OK] Request completed in {elapsed:.3f} seconds")
        print(f"[OK] Status code: {response.status_code}")
        print(f"[OK] Response: {response.text}")
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] REQUEST TIMED OUT after {elapsed:.3f} seconds")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request failed after {elapsed:.3f} seconds: {str(e)}")

def test_get_health():
    """Test GET endpoint for comparison"""
    
    url = "http://localhost:8000/debug/health"
    
    print(f"\nTesting GET endpoint for comparison: {url}")
    
    start_time = time.time()
    
    try:
        response = requests.get(
            url, 
            timeout=15  # 15 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"[OK] Request completed in {elapsed:.3f} seconds")
        print(f"[OK] Status code: {response.status_code}")
        print(f"[OK] Response: {response.text}")
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] REQUEST TIMED OUT after {elapsed:.3f} seconds")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request failed after {elapsed:.3f} seconds: {str(e)}")

if __name__ == "__main__":
    print("Testing POST timeout issue with minimal endpoints...")
    print("=" * 60)
    
    # Test GET first for comparison
    test_get_health()
    
    # Test minimal POST
    test_minimal_post()
    
    # Test POST with data
    test_with_data_post()
    
    print("\n" + "=" * 60)
    print("Test completed")