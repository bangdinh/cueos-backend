import pytest
from domain.store.value_objects import Role, can_assign_role

def test_role_hierarchy_super_admin():
    # SUPER_ADMIN cannot directly assign roles in a store
    assert can_assign_role(Role.SUPER_ADMIN, Role.OWNER) == False
    assert can_assign_role(Role.SUPER_ADMIN, Role.MANAGER) == False
    assert can_assign_role(Role.SUPER_ADMIN, Role.STAFF) == False

def test_can_assign_role_owner():
    # OWNER can assign lower roles
    assert can_assign_role(Role.OWNER, Role.MANAGER) == True
    assert can_assign_role(Role.OWNER, Role.STAFF) == True
    # OWNER cannot assign same or higher roles
    assert can_assign_role(Role.OWNER, Role.OWNER) == False
    assert can_assign_role(Role.OWNER, Role.SUPER_ADMIN) == False

def test_can_assign_role_manager():
    # MANAGER can assign STAFF
    assert can_assign_role(Role.MANAGER, Role.STAFF) == True
    # MANAGER cannot assign MANAGER, OWNER, etc.
    assert can_assign_role(Role.MANAGER, Role.MANAGER) == False
    assert can_assign_role(Role.MANAGER, Role.OWNER) == False

def test_can_assign_role_staff():
    # STAFF cannot assign anyone
    assert can_assign_role(Role.STAFF, Role.STAFF) == False
    assert can_assign_role(Role.STAFF, Role.MANAGER) == False
