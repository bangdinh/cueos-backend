class StoreDomainError(Exception):
    """Ngoại lệ gốc của domain store."""
    pass

class CrossStoreAccessError(StoreDomainError):
    """Ngoại lệ khi cố truy cập/thao tác dữ liệu chéo giữa các cửa hàng con."""
    def __init__(self, target_store_id: int, user_store_id: int = None, message: str = None):
        if not message:
            if user_store_id is not None:
                message = f"Không có quyền truy cập cửa hàng {target_store_id} từ cửa hàng {user_store_id}."
            else:
                message = f"Không có quyền truy cập cửa hàng {target_store_id}."
        super().__init__(message)

class ReadOnlyHQViolationError(StoreDomainError):
    """Ngoại lệ khi Máy Mẹ (HQ) cố thao tác ghi/sửa dữ liệu nghiệp vụ của quán con."""
    def __init__(self, message: str = "Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu, không được phép ghi/sửa dữ liệu nghiệp vụ."):
        super().__init__(message)
