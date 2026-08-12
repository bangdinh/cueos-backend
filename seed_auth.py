from microservices.auth_service.database import SessionLocal, init_db
from microservices.auth_service.models.user import UserModel, UserRole

init_db()
db = SessionLocal()

admin = db.query(UserModel).filter(UserModel.username == "admin").first()
if not admin:
    admin = UserModel(username="admin", password_hash="secret")
    db.add(admin)
    db.commit()
    db.add((user_id=admin.id, store_id=1, role=UserRole.SUPER_ADMIN.value))
    print("Added admin")
    
mgr = db.query(UserModel).filter(UserModel.username == "manager1").first()
if not mgr:
    mgr = UserModel(username="manager1", password_hash="secret")
    db.add(mgr)
    db.commit()
    db.add((user_id=mgr.id, store_id=1, role=UserRole.ADMIN.value))
    print("Added manager1")
    
staff = db.query(UserModel).filter(UserModel.username == "staff1").first()
if not staff:
    staff = UserModel(username="staff1", password_hash="secret")
    db.add(staff)
    db.commit()
    db.add((user_id=staff.id, store_id=1, role=UserRole.MANAGER.value))
    print("Added staff1")

db.commit()
db.close()
