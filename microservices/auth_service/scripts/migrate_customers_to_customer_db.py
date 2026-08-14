"""
Migration Script: Tách bảng customers từ auth.db sang customer.db riêng.
"""
import os
import sqlite3
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "auth.db")
CUSTOMER_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "customer.db")

def migrate_customers():
    print("=" * 60)
    print("🚀 MIGRATION: SEPARATING customers FROM auth.db TO customer.db")
    print("=" * 60)
    
    # 1. Kết nối auth.db
    auth_conn = sqlite3.connect(AUTH_DB_PATH)
    auth_cursor = auth_conn.cursor()
    
    # 2. Tạo customer.db với schema mới
    cust_conn = sqlite3.connect(CUSTOMER_DB_PATH)
    cust_cursor = cust_conn.cursor()
    
    cust_cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) UNIQUE,
        points INTEGER DEFAULT 0,
        created_at DATETIME,
        updated_at DATETIME
    );
    """)
    cust_cursor.execute("CREATE INDEX IF NOT EXISTS ix_customers_id ON customers(id);")
    cust_cursor.execute("CREATE INDEX IF NOT EXISTS ix_customers_store_id ON customers(store_id);")
    cust_cursor.execute("CREATE INDEX IF NOT EXISTS ix_customers_name ON customers(name);")
    cust_cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_customers_phone ON customers(phone);")
    cust_conn.commit()
    print("✅ Đã tạo bảng customers trong customer.db thành công")
    
    # 3. Kiểm tra xem auth.db có bảng customers không
    auth_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
    if auth_cursor.fetchone():
        # Lấy dữ liệu từ auth.db
        auth_cursor.execute("SELECT id, store_id, name, phone, points, created_at, updated_at FROM customers")
        rows = auth_cursor.fetchall()
        count_before = len(rows)
        print(f"📊 Tìm thấy {count_before} dòng dữ liệu trong auth.db.customers")
        
        # Insert vào customer.db
        for row in rows:
            cust_cursor.execute("""
            INSERT OR REPLACE INTO customers (id, store_id, name, phone, points, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, row)
        cust_conn.commit()
        
        # So khớp COUNT(*)
        cust_cursor.execute("SELECT COUNT(*) FROM customers")
        count_after = cust_cursor.fetchone()[0]
        print(f"📊 Số dòng trong customer.db.customers sau migrate: {count_after}")
        assert count_before == count_after, f"Số lượng không khớp: {count_before} != {count_after}"
        print(f"✅ Xác thực COUNT(*) khớp 100% ({count_before} = {count_after})")
        
        # 4. DROP TABLE customers khỏi auth.db
        auth_cursor.execute("DROP TABLE IF EXISTS customers")
        auth_conn.commit()
        print("🗑️ Đã DROP TABLE customers khỏi auth.db thành công")
    else:
        print("ℹ️ auth.db không có bảng customers")
        
    auth_conn.close()
    cust_conn.close()
    print("=" * 60)
    print("🎉 HOÀN TẤT MIGRATION customers SANG customer.db")
    print("=" * 60)

if __name__ == "__main__":
    migrate_customers()
