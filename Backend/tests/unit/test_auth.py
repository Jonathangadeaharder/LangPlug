"""Test authentication endpoints"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test GET /health endpoint"""
    print(f"[{datetime.now()}] Testing GET /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_register():
    """Test POST /auth/register endpoint"""
    print(f"\n[{datetime.now()}] Testing POST /auth/register...")
    try:
        data = {
            "username": f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=data, timeout=5)
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_login():
    """Test POST /auth/login endpoint"""
    print(f"\n[{datetime.now()}] Testing POST /auth/login...")
    
    # First register a user
    username = f"logintest_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    password = "testpass123"
    
    print(f"Registering user: {username}")
    register_data = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=5)
        if response.status_code not in [200, 201]:
            print(f"Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"Registration error: {e}")
        return False
    
    # Now try to login
    print(f"Logging in as: {username}")
    try:
        login_data = {
            "username": username,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Login error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing LangPlug Authentication")
    print("=" * 60)
    
    # Test endpoints
    health_ok = test_health()
    register_ok = test_register()
    login_ok = test_login()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Health Check (GET): {'PASSED' if health_ok else 'FAILED'}")
    print(f"  Register (POST): {'PASSED' if register_ok else 'FAILED'}")
    print(f"  Login (POST): {'PASSED' if login_ok else 'FAILED'}")
    print("=" * 60)
    
    if health_ok and register_ok and login_ok:
        print("\nSUCCESS: All authentication endpoints are working!")
        print("POST request timeout issue has been FIXED!")
    else:
        print("\nFAILURE: Some endpoints are still not working")