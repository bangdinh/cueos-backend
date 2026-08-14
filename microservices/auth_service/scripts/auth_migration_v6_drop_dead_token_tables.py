"""
Migration Script v6: Xóa bỏ 2 bảng dead schema (refresh_tokens, password_reset_tokens) khỏi auth.db.
Chạy: python -m microservices.auth_service.scripts.auth_migration_v6_drop_dead_token_tables
"""
import os
import sqlite3
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "auth.db")

def run_migration():
    print("=" * 60)
    print("🧹 DATABASE MIGRATION V6: DROP DEAD TOKEN TABLES IN AUTH.DB")
    print("=" * 60)
    
    if not os.path.exists(AUTH_DB_PATH):
        print(f"⚠️ Không tìm thấy file {AUTH_DB_PATH}")
        return False
        
    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Drop refresh_tokens
        cursor.execute("DROP TABLE IF EXISTS refresh_tokens")
        print("🗑️ [ĐÃ XÓA] Bảng refresh_tokens")
        
        # 2. Drop password_reset_tokens
        cursor.execute("DROP TABLE IF EXISTS password_reset_tokens")
        print("🗑️ [ĐÃ XÓA] Bảng password_reset_tokens")
        
        conn.commit()
        
        # 3. Liệt kê lại các bảng còn lại trong auth.db
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        print("\n" + "-" * 60)
        print("📊 DANH SÁCH BẢNG CÒN LẠI TRONG AUTH.DB (CHUẨN 6 BẢNG):")
        for t in sorted(tables):
            print(f"  ✅ {t}")
        print("=" * 60)
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Lỗi migration: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
