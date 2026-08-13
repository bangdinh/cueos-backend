import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'auth.db'))

def migrate():
    print(f"Migrating {DB_PATH} (Auth v6 Staff Creation)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Adding force_password_change to users...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN force_password_change BOOLEAN NOT NULL DEFAULT 1")
        except sqlite3.OperationalError as e:
            print(f"users force_password_change: {e}")

        print("Adding created_by to users...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN created_by INTEGER REFERENCES users(id) NULL")
        except sqlite3.OperationalError as e:
            print(f"users created_by: {e}")

        conn.commit()
        print("Auth Migration v6 successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
