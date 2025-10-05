import sqlite3

# Connect to the database
conn = sqlite3.connect("data/langplug.db")
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "=" * 50)
print("Users in database:")
print("=" * 50)

# Get all users
try:
    cursor.execute("SELECT id, username, email, is_active, is_verified, is_superuser, hashed_password FROM users")
    users = cursor.fetchall()

    if not users:
        print("No users found in database")
    else:
        print(f"\nFound {len(users)} user(s):\n")
        for user in users:
            print(f"ID: {user[0]}")
            print(f"  Username: {user[1]}")
            print(f"  Email: {user[2]}")
            print(f"  Active: {user[3]}")
            print(f"  Verified: {user[4]}")
            print(f"  Superuser: {user[5]}")
            print(f"  Password Hash: {user[6][:60]}...")
            print()
except Exception as e:
    print(f"Error querying users: {e}")

conn.close()
