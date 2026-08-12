import sqlite3

def rollback_auth_db():
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    # 1. Thêm cột store_id và role vào bảng users
    print("Thêm cột store_id và role vào users...")
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN store_id INTEGER REFERENCES stores(id)")
    except Exception as e:
        print(f"Bỏ qua thêm store_id (có thể đã tồn tại): {e}")
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'CASHIER'")
    except Exception as e:
        print(f"Bỏ qua thêm role (có thể đã tồn tại): {e}")
        
    # 2. Hút dữ liệu từ user_store_roles sang users
    print("Khôi phục dữ liệu từ user_store_roles...")
    cursor.execute("SELECT user_id, store_id, role FROM user_store_roles")
    rows = cursor.fetchall()
    
    for user_id, store_id, role in rows:
        if role == 'OWNER':
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            # Cập nhật bảng stores để set owner_id
            if store_id:
                cursor.execute("UPDATE stores SET owner_id = ? WHERE id = ?", (user_id, store_id))
        else:
            cursor.execute("UPDATE users SET store_id = ?, role = ? WHERE id = ?", (store_id, role, user_id))
            
    # 3. Tiêu huỷ bảng user_store_roles
    print("Tiêu huỷ bảng user_store_roles...")
    try:
        cursor.execute("DROP TABLE user_store_roles")
    except Exception as e:
        print(f"Bỏ qua DROP TABLE: {e}")
        
    # 4. Đảm bảo owner_id có trên stores
    try:
        cursor.execute("ALTER TABLE stores ADD COLUMN owner_id INTEGER REFERENCES users(id)")
    except Exception as e:
        pass # Có thể đã có

    conn.commit()
    conn.close()
    print("Hoàn tất Rollback auth.db!")

if __name__ == '__main__':
    rollback_auth_db()
