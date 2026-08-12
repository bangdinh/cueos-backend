from enum import Enum

class Role(Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    STORE_MANAGER = "STORE_MANAGER"
    CASHIER = "CASHIER"
    STAFF = "STAFF"

    def is_hq(self) -> bool:
        return self.value == "SUPER_ADMIN"


class StoreStatus(Enum):
    """
    DDD Value Object: Trạng thái hoạt động của cửa hàng.
    """
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"
