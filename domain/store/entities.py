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
class UserStoreRoleEntity:
    store_id: int
    role: Role

@dataclass
class User:
    """
    DDD Entity: Người dùng hệ thống (Nhân viên, Quản lý, Chủ chuỗi hoặc Admin).
    """
    user_id: int
    username: str
    store_roles: list[UserStoreRoleEntity] = field(default_factory=list)
    owned_store_ids: list[int] = field(default_factory=list)
    
    def _is_hq(self) -> bool:
        return any(sr.role.is_hq() for sr in self.store_roles)
        
    def _is_owner(self) -> bool:
        return any(sr.role == Role.OWNER for sr in self.store_roles)
    
    def can_access_all_stores(self) -> bool:
        return self._is_hq()
        
    def can_write_to_store(self, store_id: int) -> bool:
        if self._is_hq():
            return False  # HQ (SUPER_ADMIN) chỉ đọc, không được ghi
        if self._is_owner():
            return store_id in self.owned_store_ids
        return any(sr.store_id == store_id for sr in self.store_roles)
        
    def validate_write_access(self, target_store_id: int):
        """
        Kiểm tra quyền ghi vào cửa hàng target_store_id.
        Ném ngoại lệ nghiệp vụ nếu vi phạm.
        """
        if self._is_hq():
            raise ReadOnlyHQViolationError()
            
        if self._is_owner():
            if target_store_id not in self.owned_store_ids:
                raise CrossStoreAccessError(target_store_id=target_store_id, user_store_id=None)
            return

        if not self.can_write_to_store(target_store_id):
            # Extract first store for error message backward compat
            first_store = self.store_roles[0].store_id if self.store_roles else None
            raise CrossStoreAccessError(target_store_id=target_store_id, user_store_id=first_store)
