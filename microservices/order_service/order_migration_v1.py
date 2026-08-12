import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'order.db'))

def migrate():
    print(f"Migrating {DB_PATH} (Order v1)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add updated_at to session_order_items
        print("Adding updated_at to session_order_items...")
        try:
            cursor.execute("ALTER TABLE session_order_items ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError as e:
            print(f"session_order_items updated_at: {e}")

        # 2. Triggers for updated_at
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_soi_updated_at
            AFTER UPDATE ON session_order_items
            FOR EACH ROW
            BEGIN
                UPDATE session_order_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)

        # 3. Indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_order_items_store ON session_order_items(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_order_items_session ON session_order_items(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_order_items_product ON session_order_items(product_id)")

        conn.commit()
        print("Order Migration v1 successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
