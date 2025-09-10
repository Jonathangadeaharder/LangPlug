"""Test if server is responding to requests"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test GET /health endpoint"""
    print(f"[{datetime.now()}] Testing GET /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[{datetime.now()}] Response Status: {response.status_code}")
        print(f"[{datetime.now()}] Response: {response.json()}")
        return True
    except requests.exceptions.Timeout:
        print(f"[{datetime.now()}] Request timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
        return False

def test_login():
    """Test POST /auth/login endpoint"""
    print(f"\n[{datetime.now()}] Testing POST /auth/login...")
    try:
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=data, timeout=5)
        print(f"[{datetime.now()}] Response Status: {response.status_code}")
        print(f"[{datetime.now()}] Response: {response.text}")
        return True
    except requests.exceptions.Timeout:
        print(f"[{datetime.now()}] Request timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
        return False

def test_register():
    """Test POST /auth/register endpoint"""
    print(f"\n[{datetime.now()}] Testing POST /auth/register...")
    try:
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=data, timeout=5)
        print(f"[{datetime.now()}] Response Status: {response.status_code}")
        print(f"[{datetime.now()}] Response: {response.text}")
        return True
    except requests.exceptions.Timeout:
        print(f"[{datetime.now()}] Request timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing LangPlug Server")
    print("=" * 60)
    
    # Test GET request
    health_ok = test_health()
    
    # Test POST requests
    login_ok = test_login()
    register_ok = test_register()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Health Check (GET): {'✓ PASSED' if health_ok else '✗ FAILED'}")
    print(f"  Login (POST): {'✓ PASSED' if login_ok else '✗ FAILED'}")
    print(f"  Register (POST): {'✓ PASSED' if register_ok else '✗ FAILED'}")
    print("=" * 60)