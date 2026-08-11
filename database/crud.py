from sqlalchemy.orm import Session
from database.models import BilliardTable, PlaySession, AIEvent, StaffNotification, TableStatus, NotificationStatus, Product, StoreModel
from datetime import datetime
import math

def get_active_tables(db: Session, store_id: int = 1):
    """Lấy danh sách bàn theo chi nhánh (Tenant Isolation)."""
    return db.query(BilliardTable).filter(BilliardTable.store_id == store_id).all()

def get_hq_all_tables(db: Session):
    """[HQ READ-ONLY] Lấy danh sách toàn bộ bàn của tất cả các chi nhánh."""
    return db.query(BilliardTable).all()

def get_products_by_store(db: Session, store_id: int = 1):
    """Lấy danh sách menu đồ uống theo chi nhánh."""
    return db.query(Product).filter(Product.store_id == store_id).all()

def get_hq_all_products(db: Session):
    """[HQ READ-ONLY] Lấy danh sách toàn bộ menu đồ uống trên tất cả các chi nhánh."""
    return db.query(Product).all()

def get_unsynced_completed_sessions(db: Session, store_id: int = 1):
    """Lấy các hóa đơn đã chốt ca nhưng chưa đồng bộ 1 chiều lên Máy Mẹ."""
    return db.query(PlaySession).filter(
        PlaySession.store_id == store_id,
        PlaySession.status == "COMPLETED",
        PlaySession.is_synced_to_hq == False
    ).all()

def get_hq_all_sessions(db: Session):
    """[HQ READ-ONLY] Lấy danh sách toàn bộ hóa đơn từ tất cả chi nhánh."""
    return db.query(PlaySession).all()

def seed_initial_tables(db: Session, store_id: int = 1):
    if db.query(BilliardTable).filter(BilliardTable.store_id == store_id).count() == 0:
        prefix = f"Q{store_id} - " if store_id > 1 else ""
        db.add(BilliardTable(name=f"{prefix}Bàn 1", camera_url=f"{store_id}0", price_per_hour=50000.0, table_tier="STANDARD", table_type="LIP", store_id=store_id))
        db.add(BilliardTable(name=f"{prefix}Bàn 2", camera_url=f"{store_id}1", price_per_hour=70000.0, table_tier="VIP", table_type="LIP", store_id=store_id))
        db.add(BilliardTable(name=f"{prefix}Bàn 3", camera_url=f"{store_id}2", price_per_hour=60000.0, table_tier="STANDARD", table_type="3C", store_id=store_id))
        db.add(BilliardTable(name=f"{prefix}Bàn 4", camera_url=f"{store_id}3", price_per_hour=80000.0, table_tier="VIP", table_type="3C", store_id=store_id))
        if store_id == 1:
            db.add(BilliardTable(name="Bàn 5 (Bida Lỗ)", camera_url="4", price_per_hour=60000.0, table_tier="STANDARD", table_type="POOL", store_id=store_id))
            db.add(BilliardTable(name="Bàn 6 (Bida Lỗ VIP)", camera_url="5", price_per_hour=80000.0, table_tier="VIP", table_type="POOL", store_id=store_id))
        db.commit()

def seed_initial_products(db: Session, store_id: int = 1):
    if db.query(Product).filter(Product.store_id == store_id).count() == 0:
        mult = store_id
        prefix = f"[Q{store_id}] " if store_id > 1 else ""
        db.add(Product(name=f"{prefix}Sting dâu", price=15000.0, stock=10 * mult + 5, category="Thức uống", store_id=store_id))
        db.add(Product(name=f"{prefix}Coca Cola", price=15000.0, stock=15 * mult + 2, category="Thức uống", store_id=store_id))
        db.add(Product(name=f"{prefix}Bò húc", price=20000.0, stock=20 * mult, category="Thức uống", store_id=store_id))
        db.add(Product(name=f"{prefix}Khô mực nướng", price=50000.0, stock=8 * mult, category="Đồ ăn", store_id=store_id))
        db.add(Product(name=f"{prefix}Đậu phộng rang", price=15000.0, stock=12 * mult, category="Đồ ăn", store_id=store_id))
        db.add(Product(name=f"{prefix}Thuốc lá Mèo", price=20000.0, stock=10 * mult, category="Thuốc lá", store_id=store_id))
        db.add(Product(name=f"{prefix}Khăn lạnh", price=5000.0, stock=50 * mult, category="Dịch vụ khác", store_id=store_id))
        db.commit()


def save_ai_event(db: Session, table_id: int, event_type: str, confidence: float, store_id: int = 1):
    new_event = AIEvent(table_id=table_id, event_type=event_type, confidence_score=confidence, store_id=store_id)
    db.add(new_event)
    
    if event_type == "HAND_RAISED":
        new_notif = StaffNotification(table_id=table_id, notification_type="ORDER_FOOD", store_id=store_id)
        db.add(new_notif)
        
    db.commit()
