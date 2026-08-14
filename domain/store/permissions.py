from enum import Enum
from typing import Dict, List

class StandardPermission(str, Enum):
    VIEW_INVENTORY = "perm:view_inventory"
    MANAGE_INVENTORY = "perm:manage_inventory"
    VIEW_REVENUE = "perm:view_revenue"
    APPROVE_REFUND = "perm:approve_refund"
    MANAGE_STAFF = "perm:manage_staff"
    CHECKOUT = "perm:checkout"
    MANAGE_TABLES = "perm:manage_tables"
    VIEW_OWN_SHIFT = "perm:view_own_shift"

PERMISSION_DESCRIPTIONS: Dict[StandardPermission, str] = {
    StandardPermission.VIEW_INVENTORY: "Xem danh sách và số lượng kho hàng, sản phẩm",
    StandardPermission.MANAGE_INVENTORY: "Thêm, sửa, xóa, nhập xuất kho hàng và giá sản phẩm",
    StandardPermission.VIEW_REVENUE: "Xem báo cáo doanh thu, thống kê chi nhánh và hệ thống",
    StandardPermission.APPROVE_REFUND: "Duyệt hoàn tiền, hủy phiên chơi và điều chỉnh hóa đơn",
    StandardPermission.MANAGE_STAFF: "Quản lý nhân sự, tạo tài khoản và gán quyền chi nhánh",
    StandardPermission.CHECKOUT: "Thu ngân, in hóa đơn và hoàn tất thanh toán",
    StandardPermission.MANAGE_TABLES: "Mở, đóng, chuyển bàn và quản lý các dịch vụ tại bàn chơi",
    StandardPermission.VIEW_OWN_SHIFT: "Xem ca làm việc và thống kê phiên trực của chính mình",
}

ALL_PERMISSIONS: List[str] = [p.value for p in StandardPermission]

def is_valid_permission(perm: str) -> bool:
    """Kiểm tra mã quyền có thuộc danh mục permission hạt nhân chuẩn không."""
    return perm in ALL_PERMISSIONS

def get_all_permissions_metadata() -> List[Dict[str, str]]:
    """Trả về danh sách metadata của toàn bộ permissions phục vụ API và UI."""
    return [
        {
            "permission": p.value,
            "name": p.name,
            "description": PERMISSION_DESCRIPTIONS[p]
        }
        for p in StandardPermission
    ]
