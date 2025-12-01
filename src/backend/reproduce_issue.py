import asyncio
import os
import json
import sys

# Add current directory to sys.path so we can import core
sys.path.append(os.getcwd())

# Mock environment variables BEFORE importing database module
os.environ["TESTING"] = "1"
os.environ["LANGPLUG_DATABASE_URL"] = "sqlite+aiosqlite:///./test_repro.db"
os.environ["LANGPLUG_SECRET_KEY"] = "test_secret_key_repro_must_be_32_chars_long"
os.environ["TEST_DATA"] = json.dumps({
    "users": [
        {"username": "testuser", "email": "test@example.com", "password": "password123", "role": "user"},
        {"username": "student1", "email": "student1@example.com", "password": "password123", "role": "user"},
        {"username": "teacher1", "email": "teacher1@example.com", "password": "password123", "role": "moderator"}
    ]
})

from core.database.database import init_db
from core.auth.auth_dependencies import init_auth_services

async def main():
    print("Starting reproduction script...")
    try:
        if os.path.exists("./test_repro.db"):
            os.remove("./test_repro.db")
            
        init_auth_services()
        await init_db()
        print("SUCCESS: init_db completed without error.")
    except Exception as e:
        print(f"FAILURE: init_db failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
