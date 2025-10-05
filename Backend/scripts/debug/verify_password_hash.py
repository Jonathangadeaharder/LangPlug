"""Verify if stored password hash matches expected password"""

import sqlite3

from passlib.context import CryptContext

# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Expected password
EXPECTED_PASSWORD = "AdminPass123!"

# Connect to database
conn = sqlite3.connect("data/langplug.db")
cursor = conn.cursor()

# Get admin user's password hash
cursor.execute("SELECT username, email, hashed_password FROM users WHERE username='admin'")
user = cursor.fetchone()

if user:
    username, email, stored_hash = user
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Stored Hash: {stored_hash[:60]}...")
    print("-" * 50)

    # Verify password
    is_valid = pwd_context.verify(EXPECTED_PASSWORD, stored_hash)

    if is_valid:
        print(f"[SUCCESS] Password '{EXPECTED_PASSWORD}' matches stored hash!")
    else:
        print(f"[FAILED] Password '{EXPECTED_PASSWORD}' does NOT match stored hash")
        print("\nTrying other common passwords:")

        # Try other possible passwords
        common_passwords = [
            "admin",
            "Admin123!",
            "AdminPass123",
            "admin123",
            "TestPassword123!",
            "SecurePass123!",
        ]

        for pwd in common_passwords:
            if pwd_context.verify(pwd, stored_hash):
                print(f"[FOUND] Password is: '{pwd}'")
                break
        else:
            print("[NOT FOUND] Password is not in common list")
else:
    print("Admin user not found in database")

conn.close()
