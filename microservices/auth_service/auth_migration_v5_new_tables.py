import sqlite3
import os
import sys

# Adjust the path based on project structure
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'auth.db'))

def up():
    print(f"Migrating UP {DB_PATH} (Auth v5 - Security Tables)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add security columns to users
        print("Adding security columns to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until DATETIME")
            cursor.execute("ALTER TABLE users ADD COLUMN last_login_at DATETIME")
        except sqlite3.OperationalError as e:
            print(f"Skipping adding columns (might already exist): {e}")

        # 2. Create new tables
        print("Creating security tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                token_hash VARCHAR(255) NOT NULL,
                device_info VARCHAR(255),
                expires_at DATETIME NOT NULL,
                revoked_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                token_hash VARCHAR(255) NOT NULL,
                expires_at DATETIME NOT NULL,
                used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                store_id INTEGER REFERENCES stores(id),
                action VARCHAR(100) NOT NULL,
                target_type VARCHAR(100) NOT NULL,
                target_id INTEGER NOT NULL,
                ip_address VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL REFERENCES stores(id),
                phone VARCHAR(20) NOT NULL,
                role VARCHAR(50) NOT NULL,
                token VARCHAR(255) NOT NULL,
                invited_by INTEGER NOT NULL REFERENCES users(id),
                expires_at DATETIME NOT NULL,
                accepted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("Migration UP completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration UP failed: {e}")
    finally:
        conn.close()

def down():
    print(f"Migrating DOWN {DB_PATH} (Auth v5 - Security Tables)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Drop security tables
        print("Dropping security tables...")
        cursor.execute("DROP TABLE IF EXISTS staff_invitations")
        cursor.execute("DROP TABLE IF EXISTS audit_logs")
        cursor.execute("DROP TABLE IF EXISTS password_reset_tokens")
        cursor.execute("DROP TABLE IF EXISTS refresh_tokens")

        # 2. Drop columns from users
        print("Dropping security columns from users table...")
        try:
            cursor.execute("ALTER TABLE users DROP COLUMN failed_login_attempts")
            cursor.execute("ALTER TABLE users DROP COLUMN locked_until")
            cursor.execute("ALTER TABLE users DROP COLUMN last_login_at")
        except sqlite3.OperationalError as e:
            print(f"Could not drop columns: {e}")

        conn.commit()
        print("Migration DOWN completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration DOWN failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        down()
    else:
        up()
