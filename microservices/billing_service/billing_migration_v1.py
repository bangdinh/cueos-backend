import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'billing.db'))

def migrate():
    print(f"Migrating {DB_PATH} (Billing v1)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add columns to customers
        print("Adding columns to customers...")
        try:
            cursor.execute("ALTER TABLE customers ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError as e:
            print(f"customers updated_at: {e}")

        # 2. Add columns to staff_notifications
        print("Adding columns to staff_notifications...")
        try:
            cursor.execute("ALTER TABLE staff_notifications ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError as e:
            print(f"staff_notifications updated_at: {e}")

        # 3. Triggers
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_cust_updated_at
            AFTER UPDATE ON customers
            FOR EACH ROW
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_sn_updated_at
            AFTER UPDATE ON staff_notifications
            FOR EACH ROW
            BEGIN
                UPDATE staff_notifications SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)

        # 4. Indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_store ON customers(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_staff_notifications_store ON staff_notifications(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_staff_notifications_table ON staff_notifications(table_id)")

        conn.commit()
        print("Billing Migration v1 successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
