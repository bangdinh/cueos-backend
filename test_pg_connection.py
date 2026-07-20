import sys
import os

# Them duong dan goc vao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import init_db, engine, SessionLocal
from database.models import BilliardTable, PlaySession, AIEvent, StaffNotification
from database.crud import seed_initial_tables

def test_connection():
    print("--- KIEM TRA KET NOI POSTGRESQL ---")
    db_url = str(engine.url)
    print(f"Engine dang su dung database URL: {db_url}")
    
    if "sqlite" in db_url:
        print("[WARNING] Engine dang dung SQLite. PostgreSQL co the chua dung hoac file .env chua cau hinh password dung!")
        print("Vui long kiem tra file .env va khoi dong PostgreSQL.")
        return False
        
    try:
        print("Dang khoi tao cac bang trong PostgreSQL...")
        init_db()
        print("Khoi tao bang thanh cong!")
        
        db = SessionLocal()
        try:
            print("Dang nap du lieu ban dau (Seeding tables)...")
            seed_initial_tables(db)
            table_count = db.query(BilliardTable).count()
            print(f"Seeding thanh cong! Tong so ban trong he thong: {table_count}")
        finally:
            db.close()
            
        print("KET NOI VA KHOI TAO POSTGRESQL HOAN HAO!")
        return True
    except Exception as e:
        print(f"LOI KET NOI POSTGRESQL: {e}")
        return False

if __name__ == "__main__":
    test_connection()
