from enum import Enum

class Role(Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"

    def is_hq(self) -> bool:
        return self.value == "SUPER_ADMIN"

ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: 3,
    Role.OWNER: 2,
    Role.MANAGER: 1,
    Role.STAFF: 0
}

def can_assign_role(assigner_role: Role, target_role: Role) -> bool:
    """
    Check if the assigner_role has permission to assign the target_role.
    - SUPER_ADMIN cannot assign directly to a store.
    - An assigner can only assign roles that are strictly lower in hierarchy.
    """
    if assigner_role == Role.SUPER_ADMIN:
        return False
        
    assigner_level = ROLE_HIERARCHY.get(assigner_role, -1)
    target_level = ROLE_HIERARCHY.get(target_role, -1)
    
    return assigner_level > target_level


class StoreStatus(Enum):
    """
    DDD Value Object: Trạng thái hoạt động của cửa hàng.
    """
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"
