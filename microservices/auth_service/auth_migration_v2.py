import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'auth.db'))

def migrate():
    print(f"Migrating {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Alter Users Table
        print("Adding columns to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)")
        except sqlite3.OperationalError as e:
            print(f"full_name: {e}")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
        except sqlite3.OperationalError as e:
            print(f"phone: {e}")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        except sqlite3.OperationalError as e:
            print(f"is_active: {e}")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT '2026-08-11 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"created_at: {e}")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT '2026-08-11 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"updated_at: {e}")

        # Add UNIQUE index to phone
        print("Creating unique index on phone...")
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
        except sqlite3.OperationalError as e:
            print(f"idx_users_phone: {e}")

        # 2. Patch Data (Update Roles)
        print("Patching roles data...")
        cursor.execute("UPDATE users SET role = 'OWNER' WHERE role = 'OWNER'")
        cursor.execute("UPDATE users SET role = 'STORE_MANAGER' WHERE role = 'STORE_MANAGER'")
        print(f"Updated roles. Affected rows: {cursor.rowcount}")

        # 3. Alter Stores Table
        print("Adding columns to stores table...")
        try:
            cursor.execute("ALTER TABLE stores ADD COLUMN created_at DATETIME DEFAULT '2026-08-11 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"stores created_at: {e}")
            
        try:
            cursor.execute("ALTER TABLE stores ADD COLUMN updated_at DATETIME DEFAULT '2026-08-11 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"stores updated_at: {e}")
            
        try:
            cursor.execute("ALTER TABLE stores ADD COLUMN owner_id INTEGER REFERENCES users(id)")
        except sqlite3.OperationalError as e:
            print(f"owner_id: {e}")

        conn.commit()
        print("Migration successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
