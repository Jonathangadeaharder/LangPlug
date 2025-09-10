#!/usr/bin/env python
"""Reset admin user password to admin/admin"""

import hashlib
import secrets
from database.database_manager import DatabaseManager
from core.config import settings

def reset_admin_password():
    """Reset the admin user password to 'admin'"""
    # Get database path
    db_path = settings.get_data_path() / "vocabulary.db"
    db_manager = DatabaseManager(str(db_path))
    
    # Generate new salt and hash for password 'admin'
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f"admin{salt}".encode()).hexdigest()
    
    # Update admin user password
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        admin = cursor.fetchone()
        
        if admin:
            # Update password
            cursor.execute("""
                UPDATE users 
                SET password_hash = ?, salt = ?, is_admin = 1
                WHERE username = ?
            """, (password_hash, salt, "admin"))
            conn.commit()
            print("Admin password reset to 'admin' successfully!")
        else:
            # Create admin user
            from datetime import datetime
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, is_admin, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, 1, ?, ?)
            """, ("admin", password_hash, salt, now, now))
            conn.commit()
            print("Admin user created with password 'admin'!")

if __name__ == "__main__":
    reset_admin_password()