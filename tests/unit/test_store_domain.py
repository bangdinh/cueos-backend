import pytest

try:
    from domain.store.value_objects import Role, StoreStatus
    from domain.store.entities import Store, User, UserStoreRoleEntity
    from domain.store.exceptions import CrossStoreAccessError, ReadOnlyHQViolationError
except ImportError:
    pass

class TestStoreDomainTDD:
    """
    TDD Phase 1 (RED): Unit Test cho Domain Store và Phân quyền Role.
    """

    def test_role_value_object(self):
        """Test Role enum có đúng các quyền SUPER_ADMIN, MANAGER, STAFF."""
        assert Role.SUPER_ADMIN.value == "SUPER_ADMIN"
        assert Role.MANAGER.value == "MANAGER"
        assert Role.STAFF.value == "STAFF"
        
        assert Role.SUPER_ADMIN.is_hq() is True
        assert Role.MANAGER.is_hq() is False
        assert Role.STAFF.is_hq() is False

    def test_store_aggregate_root_creation(self):
        """Test tạo Store Aggregate Root và kiểm tra trạng thái."""
        store = Store(store_id=10, name="Bida Club Q1", address="123 Le Loi")
        assert store.store_id == 10
        assert store.name == "Bida Club Q1"
        assert store.status == StoreStatus.ACTIVE
        
        store.deactivate()
        assert store.status == StoreStatus.MAINTENANCE
        assert store.is_active() is False

    def test_user_entity_hq_vs_store_manager(self):
        """Test User entity: HQ admin có store_roles, Quán con có store_roles cố định."""
        hq_user = User(user_id=1, username="admin_hq", store_roles=[UserStoreRoleEntity(store_id=0, role=Role.SUPER_ADMIN)])
        assert hq_user.can_access_all_stores() is True
        assert hq_user.can_write_to_store(store_id=1) is False  # HQ CHỈ ĐỌC (Read-Only)
        
        store_user = User(user_id=2, username="manager_q1", store_roles=[UserStoreRoleEntity(store_id=1, role=Role.MANAGER)])
        assert store_user.can_access_all_stores() is False
        assert store_user.can_write_to_store(store_id=1) is True
        assert store_user.can_write_to_store(store_id=2) is False  # Không được sửa dữ liệu quán khác
        
    def test_user_writing_to_other_store_raises_error(self):
        """Test nếu user quán A cố ghi dữ liệu quán B sẽ ném CrossStoreAccessError."""
        store_user = User(user_id=2, username="manager_q1", store_roles=[UserStoreRoleEntity(store_id=1, role=Role.MANAGER)])
        with pytest.raises(CrossStoreAccessError) as exc_info:
            store_user.validate_write_access(target_store_id=2)
        assert "Không có quyền truy cập cửa hàng 2" in str(exc_info.value)
        
    def test_hq_writing_to_store_raises_error(self):
        """Test HQ Admin cố ghi dữ liệu sẽ ném ReadOnlyHQViolationError."""
        hq_user = User(user_id=1, username="admin_hq", store_roles=[UserStoreRoleEntity(store_id=0, role=Role.SUPER_ADMIN)])
        with pytest.raises(ReadOnlyHQViolationError) as exc_info:
            hq_user.validate_write_access(target_store_id=1)
        assert "Máy Mẹ (HQ) chỉ có quyền đọc" in str(exc_info.value)
        
    def test_owner_can_access_owned_stores(self):
        """Test Owner có thể truy cập các quán mà họ sở hữu."""
        owner_user = User(user_id=3, username="boss", store_roles=[UserStoreRoleEntity(store_id=0, role=Role.OWNER)], owned_store_ids=[1, 2])
        assert owner_user.can_write_to_store(store_id=1) is True
        assert owner_user.can_write_to_store(store_id=2) is True
        assert owner_user.can_write_to_store(store_id=3) is False
        
        # Test validate_write_access doesn't raise error for owned stores
        owner_user.validate_write_access(target_store_id=1)
        owner_user.validate_write_access(target_store_id=2)
        
        # Test validate_write_access raises error for unowned stores
        with pytest.raises(CrossStoreAccessError):
            owner_user.validate_write_access(target_store_id=3)
