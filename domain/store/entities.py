from dataclasses import dataclass, field
from typing import Optional
from .value_objects import Role, StoreStatus
from .exceptions import CrossStoreAccessError, ReadOnlyHQViolationError

@dataclass
class Store:
    """
    DDD Aggregate Root: Chi nhánh / Cửa hàng Bida.
    """
    store_id: int
    name: str
    address: str
    status: StoreStatus = StoreStatus.ACTIVE
    
    def deactivate(self):
        self.status = StoreStatus.MAINTENANCE
        
    def activate(self):
        self.status = StoreStatus.ACTIVE
        
    def is_active(self) -> bool:
        return self.status == StoreStatus.ACTIVE

@dataclass
class User:
    """
    DDD Entity: Người dùng hệ thống (Nhân viên quán con hoặc Admin Trụ sở).
    """
    user_id: int
    username: str
    role: Role
    store_id: Optional[int] = None
    
    def can_access_all_stores(self) -> bool:
        return self.role.is_hq()
        
    def can_write_to_store(self, store_id: int) -> bool:
        if self.role.is_hq():
            return False  # HQ (SUPER_ADMIN) chỉ đọc, không được ghi
        return self.store_id == store_id
        
    def validate_write_access(self, target_store_id: int):
        """
        Kiểm tra quyền ghi vào cửa hàng target_store_id.
        Ném ngoại lệ nghiệp vụ nếu vi phạm.
        """
        if self.role.is_hq():
            raise ReadOnlyHQViolationError()
        if self.store_id != target_store_id:
            raise CrossStoreAccessError(target_store_id=target_store_id, user_store_id=self.store_id)
