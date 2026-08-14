import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from microservices.auth_service.main import app
from microservices.auth_service.database import get_db
from microservices.auth_service.keycloak_auth import get_current_keycloak_user
from database.models.base import Base
from database.models.user import UserModel, UserRole, UserStoreRole
from database.models.store import StoreModel

# In-memory database with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Tạo store 1 và store 2
    store1 = StoreModel(id=1, name="Chi nhánh Quận 1")
    store2 = StoreModel(id=2, name="Chi nhánh Quận 3")
    db.add_all([store1, store2])
    
    # Tạo user owner_user (là OWNER của store 1)
    owner = UserModel(id=10, username="owner1", password_hash="pass")
    db.add(owner)
    db.flush()
    
    owner_role = UserStoreRole(user_id=owner.id, store_id=1, role=UserRole.OWNER.value)
    db.add(owner_role)
    
    # Tạo user staff_user (chỉ là STAFF ở store 1)
    staff = UserModel(id=20, username="staff1", password_hash="pass")
    db.add(staff)
    db.flush()
    staff_role = UserStoreRole(user_id=staff.id, store_id=1, role=UserRole.STAFF.value)
    db.add(staff_role)
    
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_keycloak_user, None)

def test_get_permissions_endpoint():
    res = client.get("/api/permissions")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["permissions"]) == 8
    perms = [p["permission"] for p in data["permissions"]]
    assert "perm:view_inventory" in perms
    assert "perm:manage_tables" in perms

@patch("microservices.auth_service.routes.roles.create_custom_composite_role")
def test_create_custom_role_success_by_owner(mock_kc_create):
    mock_kc_create.return_value = {
        "role_name": "STORE_1_CASHIER_ORDER",
        "display_name": "Thu ngân kiêm Order",
        "permissions": ["perm:checkout", "perm:manage_tables"]
    }
    
    app.dependency_overrides[get_current_keycloak_user] = lambda: {
        "sub": "owner1-sub",
        "preferred_username": "owner1",
        "realm_access": {"roles": []},
        "resource_access": {"bida-app": {"roles": ["OWNER"]}}
    }
    
    payload = {
        "role_name": "CASHIER_ORDER",
        "display_name": "Thu ngân kiêm Order",
        "permissions": ["perm:checkout", "perm:manage_tables"]
    }
    
    res = client.post("/api/stores/1/roles", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["role_name"] == "STORE_1_CASHIER_ORDER"
    assert data["store_id"] == 1
    assert "perm:checkout" in data["permissions"]
    mock_kc_create.assert_called_once()

def test_create_custom_role_forbidden_if_not_owner():
    app.dependency_overrides[get_current_keycloak_user] = lambda: {
        "sub": "staff1-sub",
        "preferred_username": "staff1",
        "realm_access": {"roles": []},
        "resource_access": {"bida-app": {"roles": ["STAFF"]}}
    }
    
    payload = {
        "role_name": "CASHIER_ORDER",
        "display_name": "Thu ngân kiêm Order",
        "permissions": ["perm:checkout"]
    }
    
    res = client.post("/api/stores/1/roles", json=payload)
    assert res.status_code == 403
    assert "Chỉ OWNER" in res.json()["detail"]

def test_create_custom_role_forbidden_for_different_store():
    app.dependency_overrides[get_current_keycloak_user] = lambda: {
        "sub": "owner1-sub",
        "preferred_username": "owner1",
        "realm_access": {"roles": []},
        "resource_access": {"bida-app": {"roles": ["OWNER"]}}
    }
    
    payload = {
        "role_name": "CASHIER_ORDER",
        "display_name": "Thu ngân kiêm Order",
        "permissions": ["perm:checkout"]
    }
    
    res = client.post("/api/stores/2/roles", json=payload)
    assert res.status_code == 403
    assert "Chỉ OWNER" in res.json()["detail"]

def test_create_custom_role_rejects_invalid_permissions():
    app.dependency_overrides[get_current_keycloak_user] = lambda: {
        "sub": "owner1-sub",
        "preferred_username": "owner1",
        "realm_access": {"roles": []},
        "resource_access": {"bida-app": {"roles": ["OWNER"]}}
    }
    
    payload = {
        "role_name": "TEST_ROLE",
        "display_name": "Test Role",
        "permissions": ["perm:checkout", "perm:invalid_fake_permission"]
    }
    
    res = client.post("/api/stores/1/roles", json=payload)
    assert res.status_code == 400
    assert "không hợp lệ" in res.json()["detail"]

@patch("microservices.auth_service.keycloak_admin.get_client_uuid")
@patch("microservices.auth_service.keycloak_admin.get_client_role")
@patch("microservices.auth_service.keycloak_admin.create_client_role")
@patch("microservices.auth_service.keycloak_admin.add_composite_roles")
@patch("microservices.auth_service.keycloak_admin.delete_client_role")
def test_create_custom_role_rollback_on_composite_failure(
    mock_delete, mock_add_comp, mock_create, mock_get_role, mock_get_uuid
):
    from microservices.auth_service.keycloak_admin import create_custom_composite_role
    
    mock_get_uuid.return_value = "client-uuid-123"
    mock_get_role.side_effect = [None, {"name": "perm:checkout"}]
    mock_create.return_value = {"name": "STORE_1_NEW_ROLE"}
    mock_add_comp.side_effect = RuntimeError("Keycloak Network Error")
    
    with pytest.raises(RuntimeError) as exc_info:
        create_custom_composite_role(
            role_name="STORE_1_NEW_ROLE",
            display_name="New Role",
            permissions=["perm:checkout"]
        )
    assert "Keycloak Network Error" in str(exc_info.value)
    mock_delete.assert_called_once_with("client-uuid-123", "STORE_1_NEW_ROLE")

@patch("microservices.auth_service.routes.roles.get_client_uuid")
@patch("microservices.auth_service.routes.roles.get_client_roles")
@patch("microservices.auth_service.routes.roles.get_role_composites")
def test_list_store_custom_roles(mock_get_comp, mock_get_roles, mock_get_uuid):
    mock_get_uuid.return_value = "client-uuid-123"
    mock_get_roles.return_value = [
        {"name": "STORE_1_CASHIER", "description": "Thu ngân Store 1"},
        {"name": "STORE_2_CASHIER", "description": "Thu ngân Store 2"},
        {"name": "perm:checkout", "description": "Permission"}
    ]
    mock_get_comp.return_value = [{"name": "perm:checkout"}, {"name": "perm:manage_tables"}]
    
    app.dependency_overrides[get_current_keycloak_user] = lambda: {
        "sub": "owner1-sub",
        "preferred_username": "owner1",
        "realm_access": {"roles": []},
        "resource_access": {"bida-app": {"roles": ["OWNER"]}}
    }
    
    res = client.get("/api/stores/1/roles")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["roles"]) == 1
    assert data["roles"][0]["role_name"] == "STORE_1_CASHIER"
    assert "perm:checkout" in data["roles"][0]["permissions"]
