from sqlalchemy.orm import Session
from database.models import StoreModel, UserModel, UserRole

def seed_default_store_and_users(db: Session):
    """Seed cửa hàng mặc định và các tài khoản mẫu khi migrate."""
    if db.query(StoreModel).filter(StoreModel.id == 1).count() == 0:
        default_store = StoreModel(id=1, name="Bida AI Club Q1 - Trụ sở chính", address="123 Lê Lợi, Q1, TP.HCM", phone="0901234567", status="ACTIVE")
        db.add(default_store)
        db.commit()
    if db.query(StoreModel).filter(StoreModel.id == 2).count() == 0:
        store_2 = StoreModel(id=2, name="Bida AI Club Q2 - Chi nhánh 2", address="456 Nguyễn Thị Minh Khai, Q3, TP.HCM", phone="0909998888", status="ACTIVE")
        db.add(store_2)
        db.commit()
    if db.query(StoreModel).filter(StoreModel.id == 3).count() == 0:
        store_3 = StoreModel(id=3, name="Bida AI Club Q3 - Chi nhánh 3", address="789 Võ Văn Ngân, TP Thủ Đức", phone="0903334444", status="ACTIVE")
        db.add(store_3)
        db.commit()
        
    if db.query(UserModel).filter(UserModel.username == "admin").count() == 0:
        hq_admin = UserModel(username="admin", password_hash="secret", role=UserRole.SUPER_ADMIN.value, store_id=None)
        db.add(hq_admin)
        db.commit()
    if db.query(UserModel).filter(UserModel.username == "manager1").count() == 0:
        store_mgr = UserModel(username="manager1", password_hash="secret", role=UserRole.ADMIN.value, store_id=1)
        db.add(store_mgr)
        db.commit()
    if db.query(UserModel).filter(UserModel.username == "staff1").count() == 0:
        store_staff = UserModel(username="staff1", password_hash="secret", role=UserRole.MANAGER.value, store_id=1)
        db.add(store_staff)
        db.commit()
    if db.query(UserModel).filter(UserModel.username == "manager2").count() == 0:
        store_mgr2 = UserModel(username="manager2", password_hash="secret", role=UserRole.ADMIN.value, store_id=2)
        db.add(store_mgr2)
        db.commit()
    if db.query(UserModel).filter(UserModel.username == "manager3").count() == 0:
        store_mgr3 = UserModel(username="manager3", password_hash="secret", role=UserRole.ADMIN.value, store_id=3)
        db.add(store_mgr3)
        db.commit()
