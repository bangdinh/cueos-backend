"""
Test xác nhận bảng phân quyền chuẩn theo Role — Permission Matrix.

Bảng chốt:
  SUPER_ADMIN : view_inventory, view_revenue, view_own_shift (3 quyền view)
  OWNER       : toàn bộ 8 quyền
  MANAGER     : 7 quyền — thiếu manage_staff
  STAFF       : checkout, manage_tables, view_own_shift (3 quyền vận hành)
"""
import pytest
from fastapi import HTTPException
from api.middleware.store_context import require_permission, StoreContext
from database.models import UserRole


def _make_payload(role: str, perms: list) -> dict:
    """Tạo JWT payload giả lập Keycloak đã inject Composite Role."""
    return {
        "resource_access": {
            "bida-app": {
                "roles": [role] + perms
            }
        },
        "realm_access": {"roles": []}
    }


# ---------------------------------------------------------------------------
# SUPER_ADMIN: chỉ 3 quyền view_*, không có quyền thao tác nghiệp vụ
# ---------------------------------------------------------------------------
class TestSuperAdminPermissions:
    SUPER_ADMIN_PERMS = [
        "perm:view_inventory",
        "perm:view_revenue",
        "perm:view_own_shift",
    ]
    PAYLOAD = _make_payload("SUPER_ADMIN", SUPER_ADMIN_PERMS)

    def test_super_admin_can_view_inventory(self):
        assert require_permission("perm:view_inventory", self.PAYLOAD) is True

    def test_super_admin_can_view_revenue(self):
        assert require_permission("perm:view_revenue", self.PAYLOAD) is True

    def test_super_admin_can_view_own_shift(self):
        assert require_permission("perm:view_own_shift", self.PAYLOAD) is True

    def test_super_admin_cannot_manage_inventory(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:manage_inventory", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_super_admin_cannot_manage_staff(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:manage_staff", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_super_admin_cannot_approve_refund(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:approve_refund", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_super_admin_cannot_checkout(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:checkout", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_super_admin_cannot_manage_tables(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:manage_tables", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_store_context_super_admin_has_correct_perms(self):
        ctx = StoreContext(
            store_id=None,
            role=UserRole.SUPER_ADMIN,
            user_id=1,
            permissions=self.SUPER_ADMIN_PERMS
        )
        assert ctx.has_permission("perm:view_inventory") is True
        assert ctx.has_permission("perm:view_revenue") is True
        assert ctx.has_permission("perm:view_own_shift") is True
        assert ctx.has_permission("perm:manage_staff") is False
        assert ctx.has_permission("perm:checkout") is False
        assert ctx.has_permission("perm:manage_inventory") is False


# ---------------------------------------------------------------------------
# OWNER: toàn bộ 8 quyền — bypass via OWNER role
# ---------------------------------------------------------------------------
class TestOwnerPermissions:
    ALL_8 = [
        "perm:view_inventory", "perm:manage_inventory", "perm:view_revenue",
        "perm:approve_refund", "perm:manage_staff", "perm:checkout",
        "perm:manage_tables", "perm:view_own_shift",
    ]
    PAYLOAD = _make_payload("OWNER", ALL_8)

    def test_owner_has_all_8_permissions(self):
        for perm in self.ALL_8:
            assert require_permission(perm, self.PAYLOAD) is True

    def test_store_context_owner_bypasses_permission_check(self):
        ctx = StoreContext(
            store_id=1,
            role=UserRole.OWNER,
            user_id=2,
            permissions=[]  # rỗng nhưng OWNER vẫn bypass
        )
        for perm in self.ALL_8:
            assert ctx.has_permission(perm) is True


# ---------------------------------------------------------------------------
# MANAGER: 7 quyền — KHÔNG có manage_staff
# ---------------------------------------------------------------------------
class TestManagerPermissions:
    MANAGER_PERMS = [
        "perm:view_inventory", "perm:manage_inventory", "perm:view_revenue",
        "perm:approve_refund", "perm:checkout", "perm:manage_tables",
        "perm:view_own_shift",
    ]
    PAYLOAD = _make_payload("MANAGER", MANAGER_PERMS)

    def test_manager_has_7_permissions(self):
        for perm in self.MANAGER_PERMS:
            assert require_permission(perm, self.PAYLOAD) is True

    def test_manager_cannot_manage_staff(self):
        """MANAGER không có perm:manage_staff — phải bị 403."""
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:manage_staff", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_store_context_manager_missing_manage_staff(self):
        ctx = StoreContext(
            store_id=1,
            role=UserRole.MANAGER,
            user_id=3,
            permissions=self.MANAGER_PERMS
        )
        assert ctx.has_permission("perm:manage_inventory") is True
        assert ctx.has_permission("perm:manage_staff") is False


# ---------------------------------------------------------------------------
# STAFF: chỉ 3 quyền vận hành tại bàn
# ---------------------------------------------------------------------------
class TestStaffPermissions:
    STAFF_PERMS = [
        "perm:checkout",
        "perm:manage_tables",
        "perm:view_own_shift",
    ]
    PAYLOAD = _make_payload("STAFF", STAFF_PERMS)

    def test_staff_has_3_permissions(self):
        for perm in self.STAFF_PERMS:
            assert require_permission(perm, self.PAYLOAD) is True

    def test_staff_cannot_view_inventory(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:view_inventory", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_staff_cannot_view_revenue(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:view_revenue", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_staff_cannot_manage_staff(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:manage_staff", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_staff_cannot_approve_refund(self):
        with pytest.raises(HTTPException) as exc:
            require_permission("perm:approve_refund", self.PAYLOAD)
        assert exc.value.status_code == 403

    def test_store_context_staff_only_has_operational_perms(self):
        ctx = StoreContext(
            store_id=1,
            role=UserRole.STAFF,
            user_id=5,
            permissions=self.STAFF_PERMS
        )
        assert ctx.has_permission("perm:checkout") is True
        assert ctx.has_permission("perm:manage_tables") is True
        assert ctx.has_permission("perm:view_own_shift") is True
        assert ctx.has_permission("perm:view_inventory") is False
        assert ctx.has_permission("perm:view_revenue") is False
        assert ctx.has_permission("perm:manage_inventory") is False
