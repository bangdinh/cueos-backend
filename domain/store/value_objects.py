from enum import Enum


class StoreStatus(Enum):
    """
    DDD Value Object: Trạng thái hoạt động của cửa hàng.
    """
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"
