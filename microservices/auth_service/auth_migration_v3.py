import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'auth.db'))

def migrate():
    print(f"Migrating {DB_PATH} (Auth v3)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create user_store_roles table
        print("Creating user_store_roles table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_store_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                store_id INTEGER NOT NULL REFERENCES stores(id),
                role VARCHAR(50) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usr_user_store ON user_store_roles(user_id, store_id)")
        
        # Trigger for updated_at
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_usr_updated_at
            AFTER UPDATE ON user_store_roles
            FOR EACH ROW
            BEGIN
                UPDATE user_store_roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)

        # 2. Add deleted_at to users
        print("Adding deleted_at to users...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN deleted_at DATETIME NULL")
        except sqlite3.OperationalError as e:
            print(f"users deleted_at: {e}")

        # 3. Patch Data: move store_id and role to user_store_roles
        print("Migrating data to user_store_roles...")
        # Since older users have store_id and role
        try:
            cursor.execute("SELECT id, store_id, role FROM users WHERE store_id IS NOT NULL")
            rows = cursor.fetchall()
            for row in rows:
                user_id, store_id, role = row
                try:
                    cursor.execute(
                        "INSERT INTO user_store_roles (user_id, store_id, role) VALUES (?, ?, ?)",
                        (user_id, store_id, role)
                    )
                except sqlite3.IntegrityError:
                    pass # Already exists
        except sqlite3.OperationalError:
            print("store_id or role might already be removed.")
                
        # 4. Remove store_id and role from users
        # SQLite drop column is supported in 3.35.0+, let's try ALTER TABLE DROP COLUMN
        print("Dropping store_id and role from users...")
        try:
            cursor.execute("ALTER TABLE users DROP COLUMN store_id")
        except sqlite3.OperationalError as e:
            print(f"Cannot drop store_id (might need older sqlite workaround or already dropped): {e}")
            
        try:
            cursor.execute("ALTER TABLE users DROP COLUMN role")
        except sqlite3.OperationalError as e:
            print(f"Cannot drop role: {e}")

        conn.commit()
        print("Auth Migration v3 successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
