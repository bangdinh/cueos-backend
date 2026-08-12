import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inventory.db'))

def migrate():
    print(f"Migrating {DB_PATH} (Inventory v1)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add deleted_at to products
        print("Adding deleted_at to products...")
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN deleted_at DATETIME NULL")
        except sqlite3.OperationalError as e:
            print(f"products deleted_at: {e}")

        # 2. Add updated_at, deleted_at to billiard_tables
        print("Adding columns to billiard_tables...")
        try:
            cursor.execute("ALTER TABLE billiard_tables ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError as e:
            print(f"billiard_tables updated_at: {e}")
            
        try:
            cursor.execute("ALTER TABLE billiard_tables ADD COLUMN deleted_at DATETIME NULL")
        except sqlite3.OperationalError as e:
            print(f"billiard_tables deleted_at: {e}")

        # 3. Triggers for updated_at
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_bt_updated_at
            AFTER UPDATE ON billiard_tables
            FOR EACH ROW
            BEGIN
                UPDATE billiard_tables SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)

        # 4. Indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_store ON products(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_billiard_tables_store ON billiard_tables(store_id)")

        conn.commit()
        print("Inventory Migration v1 successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
