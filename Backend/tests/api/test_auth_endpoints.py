#!/usr/bin/env python3
"""
Test authentication endpoints to verify dependency injection fix
"""
import requests
import time

def test_register_endpoint():
    """Test user registration endpoint"""
    
    url = "http://localhost:8000/auth/register"
    data = {
        "username": f"testuser_{int(time.time())}",
        "password": "testpass123"
    }
    
    print(f"Testing registration endpoint: {url}")
    print(f"Data: {data}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url, 
            json=data,
            timeout=15
        )
        
        elapsed = time.time() - start_time
        print(f"[OK] Request completed in {elapsed:.3f} seconds")
        print(f"[OK] Status code: {response.status_code}")
        print(f"[OK] Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() is not None
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] REQUEST TIMED OUT after {elapsed:.3f} seconds")
        return None
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request failed after {elapsed:.3f} seconds: {str(e)}")
        return None

def test_login_endpoint():
    """Test user login endpoint"""
    
    url = "http://localhost:8000/auth/login"
    data = {
        "username": "admin",
        "password": "admin"
    }
    
    print(f"\nTesting login endpoint: {url}")
    print(f"Data: {data}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url, 
            json=data,
            timeout=15
        )
        
        elapsed = time.time() - start_time
        print(f"[OK] Request completed in {elapsed:.3f} seconds")
        print(f"[OK] Status code: {response.status_code}")
        print(f"[OK] Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() is not None
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] REQUEST TIMED OUT after {elapsed:.3f} seconds")
        return None
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request failed after {elapsed:.3f} seconds: {str(e)}")
        return None

if __name__ == "__main__":
    print("Testing authentication endpoints to verify dependency injection fix...")
    print("=" * 70)
    
    # Test registration
    register_result = test_register_endpoint()
    
    # Test login
    login_result = test_login_endpoint()
    
    print("\n" + "=" * 70)
    
    # Summary
    if register_result or login_result:
        print("SUCCESS: At least one authentication endpoint is working!")
        print("The dependency injection fix appears to be successful.")
    else:
        print("FAILURE: Authentication endpoints are still having issues.")
    
    print("Test completed")