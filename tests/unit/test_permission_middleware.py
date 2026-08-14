import pytest
from fastapi import HTTPException
from api.middleware.store_context import StoreContext, require_permission
from database.models import UserRole

def test_require_permission_with_valid_client_role():
    payload = {
        "resource_access": {
            "bida-app": {
                "roles": ["perm:view_inventory", "perm:checkout"]
            }
        },
        "realm_access": {"roles": []}
    }
    assert require_permission("perm:view_inventory", payload) is True
    assert require_permission("perm:checkout", payload) is True

def test_require_permission_raises_403_when_missing():
    payload = {
        "resource_access": {
            "bida-app": {
                "roles": ["perm:view_inventory"]
            }
        },
        "realm_access": {"roles": []}
    }
    with pytest.raises(HTTPException) as exc_info:
        require_permission("perm:view_revenue", payload)
    assert exc_info.value.status_code == 403
    assert "Thiếu quyền" in exc_info.value.detail

def test_require_permission_owner_bypasses_all_permissions():
    """OWNER c\u00f3 to\u00e0n quy\u1ec1n \u2014 bypass m\u1ecdi require_permission."""
    owner_payload = {
        "resource_access": {"bida-app": {"roles": ["OWNER"]}},
        "realm_access": {"roles": []}
    }
    assert require_permission("perm:view_revenue", owner_payload) is True
    assert require_permission("perm:manage_staff", owner_payload) is True
    assert require_permission("perm:approve_refund", owner_payload) is True


def test_require_permission_super_admin_does_not_bypass():
    """SUPER_ADMIN KH\u00d4NG bypass \u2014 ph\u1ea3i c\u00f3 permission th\u1ef1c trong token m\u1edbi pass."""
    # SUPER_ADMIN c\u00f3 perm:view_revenue trong token (Composite Role \u0111\u00fang)
    super_admin_with_perm = {
        "resource_access": {"bida-app": {"roles": ["SUPER_ADMIN", "perm:view_revenue", "perm:view_inventory", "perm:view_own_shift"]}},
        "realm_access": {"roles": []}
    }
    assert require_permission("perm:view_revenue", super_admin_with_perm) is True
    assert require_permission("perm:view_inventory", super_admin_with_perm) is True

    # SUPER_ADMIN kh\u00f4ng c\u00f3 perm:manage_staff \u2014 ph\u1ea3i b\u1ecb 403
    with pytest.raises(HTTPException) as exc_info:
        require_permission("perm:manage_staff", super_admin_with_perm)
    assert exc_info.value.status_code == 403

    # SUPER_ADMIN kh\u00f4ng c\u00f3 perm:approve_refund \u2014 ph\u1ea3i b\u1ecb 403
    with pytest.raises(HTTPException) as exc_info:
        require_permission("perm:approve_refund", super_admin_with_perm)
    assert exc_info.value.status_code == 403

def test_require_permission_strictly_enforces_client_roles_ignores_forged_realm_role():
    # Kẻ tấn công cố tình giả mạo claim realm_access hoặc role ngoài resource_access
    forged_payload = {
        "role": "SUPER_ADMIN",  # Giả mạo top-level field
        "realm_access": {"roles": ["OWNER"]},  # Giả mạo Realm Role
        "resource_access": {
            "bida-app": {
                "roles": ["perm:view_inventory"]  # Chỉ có quyền xem kho
            }
        }
    }
    # Chỉ xem được kho
    assert require_permission("perm:view_inventory", forged_payload) is True
    
    # Bị chặn 403 khi cố truy cập quyền nhạy cảm khác dù có field role giả mạo
    with pytest.raises(HTTPException) as exc_info:
        require_permission("perm:approve_refund", forged_payload)
    assert exc_info.value.status_code == 403

def test_composite_custom_role_permissions():
    # User được Keycloak làm phẳng các composite permissions vào resource_access
    payload = {
        "resource_access": {
            "bida-app": {
                "roles": [
                    "STORE_1_THU_NGAN_KHO",
                    "perm:checkout",
                    "perm:view_inventory",
                    "perm:manage_inventory"
                ]
            }
        }
    }
    assert require_permission("perm:checkout", payload) is True
    assert require_permission("perm:view_inventory", payload) is True
    assert require_permission("perm:manage_inventory", payload) is True
    
    # Không có quyền view_revenue
    with pytest.raises(HTTPException) as exc_info:
        require_permission("perm:view_revenue", payload)
    assert exc_info.value.status_code == 403

def test_store_context_has_permission():
    ctx = StoreContext(
        store_id=1,
        role=UserRole.STAFF,
        user_id=10,
        permissions=["perm:manage_tables", "perm:checkout"]
    )
    assert ctx.has_permission("perm:manage_tables") is True
    assert ctx.has_permission("perm:checkout") is True
    assert ctx.has_permission("perm:view_revenue") is False

def test_store_context_require_permission_raises_403():
    ctx = StoreContext(
        store_id=1,
        role=UserRole.STAFF,
        user_id=10,
        permissions=["perm:manage_tables"]
    )
    # Passed
    ctx.require_permission("perm:manage_tables")
    
    # Failed
    with pytest.raises(HTTPException) as exc_info:
        ctx.require_permission("perm:manage_inventory")
    assert exc_info.value.status_code == 403
