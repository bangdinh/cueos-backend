import sqlite3
import os
import sys
from datetime import datetime

# Adjust the path based on project structure
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'auth.db'))

def up():
    print(f"Migrating UP {DB_PATH} (Auth v4 - Revert)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create user_store_roles table
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
        
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_store ON user_store_roles(user_id, store_id)")

        # 2. Migrate data from users to user_store_roles
        print("Migrating data to user_store_roles...")
        try:
            cursor.execute("SELECT id, store_id, role FROM users WHERE store_id IS NOT NULL")
            rows = cursor.fetchall()
            for row in rows:
                user_id, store_id, role = row
                cursor.execute("""
                    INSERT OR IGNORE INTO user_store_roles (user_id, store_id, role)
                    VALUES (?, ?, ?)
                """, (user_id, store_id, role))
        except sqlite3.OperationalError as e:
            print(f"Skipping data migration (columns might not exist): {e}")

        # 3. Drop store_id and role from users
        print("Dropping store_id and role from users...")
        try:
            cursor.execute("ALTER TABLE users DROP COLUMN store_id")
            cursor.execute("ALTER TABLE users DROP COLUMN role")
        except sqlite3.OperationalError as e:
            print(f"Could not drop columns (maybe already dropped or SQLite version too old): {e}")
            
        conn.commit()
        print("Migration UP completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration UP failed: {e}")
    finally:
        conn.close()

def down():
    print(f"Migrating DOWN {DB_PATH} (Auth v4 - Revert)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add store_id and role back to users
        print("Adding store_id and role back to users...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN store_id INTEGER REFERENCES stores(id)")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50)")
        except sqlite3.OperationalError as e:
            print(f"Could not add columns: {e}")

        # 2. Migrate data back (take the first role found for a user)
        print("Migrating data back to users...")
        cursor.execute("SELECT user_id, store_id, role FROM user_store_roles GROUP BY user_id")
        rows = cursor.fetchall()
        for row in rows:
            user_id, store_id, role = row
            cursor.execute("""
                UPDATE users SET store_id = ?, role = ? WHERE id = ?
            """, (store_id, role, user_id))

        # 3. Drop user_store_roles
        print("Dropping user_store_roles...")
        cursor.execute("DROP TABLE IF EXISTS user_store_roles")

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
