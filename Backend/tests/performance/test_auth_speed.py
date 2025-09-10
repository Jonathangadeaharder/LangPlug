#!/usr/bin/env python3
"""Test authentication endpoint speed"""

import requests
import time
import random

BASE_URL = "http://localhost:8000"

def test_auth_speed():
    """Test authentication endpoints for speed"""
    
    # Generate unique username
    username = f"speedtest_{random.randint(1000, 9999)}"
    password = "test123456"
    
    print(f"Testing authentication with user: {username}")
    print("-" * 50)
    
    # Test registration speed
    print("\n1. Testing REGISTRATION speed...")
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": username, "password": password},
            timeout=10
        )
        reg_time = time.time() - start
        print(f"   Registration: {response.status_code} - {reg_time:.2f} seconds")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        reg_time = time.time() - start
        print(f"   Registration FAILED after {reg_time:.2f} seconds: {e}")
    
    # Test login speed
    print("\n2. Testing LOGIN speed...")
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        login_time = time.time() - start
        print(f"   Login: {response.status_code} - {login_time:.2f} seconds")
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"   Token received: {token[:20]}..." if token else "   No token received")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        login_time = time.time() - start
        print(f"   Login FAILED after {login_time:.2f} seconds: {e}")
    
    # Test auth/me speed
    if 'token' in locals():
        print("\n3. Testing AUTH/ME speed...")
        start = time.time()
        try:
            response = requests.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            me_time = time.time() - start
            print(f"   Auth/me: {response.status_code} - {me_time:.2f} seconds")
            if response.status_code == 200:
                print(f"   User data: {response.json()}")
        except Exception as e:
            me_time = time.time() - start
            print(f"   Auth/me FAILED after {me_time:.2f} seconds: {e}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    if 'reg_time' in locals():
        print(f"  Registration: {reg_time:.2f}s")
    if 'login_time' in locals():
        print(f"  Login: {login_time:.2f}s")
    if 'me_time' in locals():
        print(f"  Auth/me: {me_time:.2f}s")
    
    # Flag delays
    print("\nDELAY ANALYSIS:")
    delays_found = False
    if 'reg_time' in locals() and reg_time > 1.0:
        print(f"  [WARNING] Registration is SLOW ({reg_time:.2f}s > 1s)")
        delays_found = True
    if 'login_time' in locals() and login_time > 1.0:
        print(f"  [WARNING] Login is SLOW ({login_time:.2f}s > 1s)")
        delays_found = True
    if 'me_time' in locals() and me_time > 0.5:
        print(f"  [WARNING] Auth/me is SLOW ({me_time:.2f}s > 0.5s)")
        delays_found = True
    
    if not delays_found:
        print("  [OK] All endpoints are responding quickly!")

if __name__ == "__main__":
    test_auth_speed()