import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'session.db'))

def migrate():
    print(f"Migrating {DB_PATH} (Session v1)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add columns to play_sessions
        print("Adding columns to play_sessions...")
        try:
            cursor.execute("ALTER TABLE play_sessions ADD COLUMN updated_at DATETIME DEFAULT '2026-08-12 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"play_sessions updated_at: {e}")

        # 2. Add columns to ai_events
        print("Adding columns to ai_events...")
        try:
            cursor.execute("ALTER TABLE ai_events ADD COLUMN updated_at DATETIME DEFAULT '2026-08-12 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"ai_events updated_at: {e}")
            
        # 3. Add columns to billiard_tables
        print("Adding columns to billiard_tables...")
        try:
            cursor.execute("ALTER TABLE billiard_tables ADD COLUMN updated_at DATETIME DEFAULT '2026-08-12 00:00:00'")
        except sqlite3.OperationalError as e:
            print(f"billiard_tables updated_at: {e}")
            
        try:
            cursor.execute("ALTER TABLE billiard_tables ADD COLUMN deleted_at DATETIME NULL")
        except sqlite3.OperationalError as e:
            print(f"billiard_tables deleted_at: {e}")

        # 4. Triggers
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_ps_updated_at
            AFTER UPDATE ON play_sessions
            FOR EACH ROW
            BEGIN
                UPDATE play_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_aie_updated_at
            AFTER UPDATE ON ai_events
            FOR EACH ROW
            BEGIN
                UPDATE ai_events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS trigger_bt_session_updated_at
            AFTER UPDATE ON billiard_tables
            FOR EACH ROW
            BEGIN
                UPDATE billiard_tables SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """)

        # 5. Indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_play_sessions_store ON play_sessions(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_play_sessions_table ON play_sessions(table_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_events_store ON ai_events(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_events_table ON ai_events(table_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_billiard_tables_store_session ON billiard_tables(store_id)")

        conn.commit()
        print("Session Migration v1 successful!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
