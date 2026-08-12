from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import UserModel, UserRole, UserStoreRole
from database.models.store import StoreModel

class UserService:
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
        """Lấy thông tin người dùng dựa trên username."""
        return db.query(UserModel).filter(UserModel.deleted_at == None).filter(UserModel.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
        """Lấy thông tin người dùng dựa trên ID."""
        return db.query(UserModel).filter(UserModel.deleted_at == None).filter(UserModel.id == user_id).first()

    @staticmethod
    def get_users_by_store(db: Session, store_id: int) -> List[UserModel]:
        return db.query(UserModel).join(UserStoreRole).filter(UserModel.deleted_at == None).filter(UserStoreRole.store_id == store_id).all()

    @staticmethod
    def is_super_admin(db: Session, user: UserModel) -> bool:
        roles = db.query(UserStoreRole).filter(UserStoreRole.user_id == user.id).all()
        return any(r.role == UserRole.SUPER_ADMIN.value for r in roles)

    @staticmethod
    def can_access_store(db: Session, user: UserModel, target_store_id: int) -> bool:
        if UserService.is_super_admin(db, user):
            return True
        
        roles = db.query(UserStoreRole).filter(UserStoreRole.user_id == user.id).all()
        if any(r.role == UserRole.OWNER.value for r in roles):
            stores = db.query(StoreModel).filter(StoreModel.owner_id == user.id).all()
            if target_store_id in [s.id for s in stores]:
                return True
                
        return any(r.store_id == target_store_id for r in roles)
