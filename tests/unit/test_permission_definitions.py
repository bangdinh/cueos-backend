import pytest
from domain.store.permissions import (
    StandardPermission,
    PERMISSION_DESCRIPTIONS,
    ALL_PERMISSIONS,
    is_valid_permission,
    get_all_permissions_metadata
)

def test_standard_permissions_contain_all_core_perms():
    expected_perms = [
        "perm:view_inventory",
        "perm:manage_inventory",
        "perm:view_revenue",
        "perm:approve_refund",
        "perm:manage_staff",
        "perm:checkout",
        "perm:manage_tables",
        "perm:view_own_shift",
    ]
    for p in expected_perms:
        assert p in ALL_PERMISSIONS
        assert is_valid_permission(p) is True

def test_invalid_permission_returns_false():
    assert is_valid_permission("perm:unknown_action") is False
    assert is_valid_permission("ADMIN") is False
    assert is_valid_permission("") is False

def test_all_permissions_have_vietnamese_descriptions():
    for p in StandardPermission:
        assert p in PERMISSION_DESCRIPTIONS
        desc = PERMISSION_DESCRIPTIONS[p]
        assert len(desc) > 5

def test_get_all_permissions_metadata():
    metadata = get_all_permissions_metadata()
    assert len(metadata) == 8
    for item in metadata:
        assert "permission" in item
        assert "name" in item
        assert "description" in item
        assert item["permission"].startswith("perm:")
