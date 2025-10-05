"""Verify admin credentials work"""

import sys

import requests

# Admin credentials from database initialization
ADMIN_EMAIL = "admin@langplug.com"
ADMIN_PASSWORD = "admin"

# API endpoint (assuming default port 8000)
API_URL = "http://localhost:8000"


def test_admin_login():
    """Test admin login credentials"""
    print("Testing admin login...")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")
    print(f"API URL: {API_URL}")
    print("-" * 50)

    try:
        # Attempt login
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": ADMIN_EMAIL,  # FastAPI-Users expects email in username field
                "password": ADMIN_PASSWORD,
            },
            timeout=5,
        )

        print(f"\nResponse Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Login successful!")
            print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"Token Type: {data.get('token_type', 'N/A')}")
            return True
        else:
            print("[FAILED] Login failed!")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API server.")
        print("Make sure the backend server is running on port 8000")
        print('Run: cd Backend && powershell.exe -Command ". api_venv/Scripts/activate; uvicorn core.app:app --reload"')
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_admin_login()
    sys.exit(0 if success else 1)
