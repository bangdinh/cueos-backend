from sqlalchemy.orm import Session
from database.models import BilliardTable, PlaySession, AIEvent, StaffNotification, TableStatus, NotificationStatus, Product
from datetime import datetime
import math

def get_active_tables(db: Session):
    return db.query(BilliardTable).all()

def seed_initial_tables(db: Session):
    if db.query(BilliardTable).count() == 0:
        db.add(BilliardTable(name="Bàn 1", camera_url="0", price_per_hour=50000.0, table_tier="STANDARD", table_type="LIP"))
        db.add(BilliardTable(name="Bàn 2", camera_url="1", price_per_hour=70000.0, table_tier="VIP", table_type="LIP"))
        db.add(BilliardTable(name="Bàn 3", camera_url="2", price_per_hour=60000.0, table_tier="STANDARD", table_type="3C"))
        db.add(BilliardTable(name="Bàn 4", camera_url="3", price_per_hour=80000.0, table_tier="VIP", table_type="3C"))
        db.commit()

def seed_initial_products(db: Session):
    if db.query(Product).count() == 0:
        db.add(Product(name="Sting dâu", price=15000.0, stock=10, category="Thức uống"))
        db.add(Product(name="Coca Cola", price=15000.0, stock=15, category="Thức uống"))
        db.add(Product(name="Bò húc", price=20000.0, stock=20, category="Thức uống"))
        db.add(Product(name="Khô mực nướng", price=50000.0, stock=8, category="Đồ ăn"))
        db.add(Product(name="Đậu phộng rang", price=15000.0, stock=12, category="Đồ ăn"))
        db.add(Product(name="Thuốc lá Mèo", price=20000.0, stock=10, category="Thuốc lá"))
        db.add(Product(name="Khăn lạnh", price=5000.0, stock=50, category="Dịch vụ khác"))
        db.commit()

def save_ai_event(db: Session, table_id: int, event_type: str, confidence: float):
    # Luu log su kien AI nhung khong tu dong start/stop tinh gio nua (nhan vien bam start bang tay)
    new_event = AIEvent(table_id=table_id, event_type=event_type, confidence_score=confidence)
    db.add(new_event)
    
    if event_type == "HAND_RAISED":
        new_notif = StaffNotification(table_id=table_id, notification_type="ORDER_FOOD")
        db.add(new_notif)
        
    db.commit()
