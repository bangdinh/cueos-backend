from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import UserModel, UserRole

class UserService:
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
        """Lấy thông tin người dùng dựa trên username."""
        return db.query(UserModel).filter(UserModel.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
        """Lấy thông tin người dùng dựa trên ID."""
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    @staticmethod
    def get_users_by_store(db: Session, store_id: int) -> List[UserModel]:
        """Lấy danh sách người dùng (nhân viên/quản lý) của một cửa hàng."""
        return db.query(UserModel).filter(UserModel.store_id == store_id).all()

    @staticmethod
    def is_super_admin(user: UserModel) -> bool:
        """Kiểm tra quyền hạn xem có phải là Trụ sở chính (SUPER_ADMIN) không."""
        return user.role == UserRole.SUPER_ADMIN.value

    @staticmethod
    def can_access_store(user: UserModel, target_store_id: int) -> bool:
        """
        Kiểm tra xem user có quyền truy cập vào dữ liệu của cửa hàng mục tiêu không.
        SUPER_ADMIN có thể truy cập mọi nơi. Quản lý/Thu ngân chỉ truy cập cửa hàng của mình.
        """
        if UserService.is_super_admin(user):
            return True
        return user.store_id == target_store_id
