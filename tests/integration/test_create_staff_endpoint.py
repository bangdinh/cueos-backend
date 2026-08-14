import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from microservices.auth_service.main import app
from microservices.auth_service.database import get_db
from database.models.base import Base
from database.models.user import UserModel, UserStoreRole
from domain.store.value_objects import Role
import jwt

# Test DB Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)

def create_test_token(user_id, role, store_id):
    payload = {
        "user_id": user_id,
        "role": role,
        "store_roles": [{"store_id": store_id, "role": role}] if role != "SUPER_ADMIN" else [],
        "force_password_change": False
    }
    return jwt.encode(payload, "BIDA_AI_SECURE_JWT_SECRET_KEY_2026_CHANGE_IN_PROD", algorithm="HS256")

def test_create_staff_success():
    token = create_test_token(user_id=1, role="OWNER", store_id=1)
    
    response = client.post(
        "/api/stores/1/staff",
        json={"phone": "0987654321", "full_name": "Nguyen Van A", "role": "STAFF"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "0987654321"
    assert "temp_password" in data
    assert "user_id" in data

    # Verify DB state
    db = TestingSessionLocal()
    user = db.query(UserModel).filter(UserModel.username == "0987654321").first()
    assert user is not None
    assert user.force_password_change is True
    assert user.created_by == 1
    
    store_role = db.query(UserStoreRole).filter(UserStoreRole.user_id == user.id, UserStoreRole.store_id == 1).first()
    assert store_role is not None
    assert store_role.role == "STAFF"
    db.close()

def test_create_staff_forbidden_hierarchy():
    # Manager trying to create Admin
    token = create_test_token(user_id=1, role="MANAGER", store_id=1)
    
    response = client.post(
        "/api/stores/1/staff",
        json={"phone": "0987654322", "full_name": "Nguyen Van B", "role": "OWNER"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "cannot assign OWNER" in response.json()["detail"]

def test_create_staff_wrong_store():
    # Admin of store 1 trying to create staff in store 2
    token = create_test_token(user_id=1, role="OWNER", store_id=1)
    
    response = client.post(
        "/api/stores/2/staff",
        json={"phone": "0987654323", "full_name": "Nguyen Van C", "role": "STAFF"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "You do not have a role in store 2" in response.json()["detail"]

def test_create_staff_super_admin_denied():
    # Super admin cannot assign directly
    token = create_test_token(user_id=1, role="SUPER_ADMIN", store_id=None)
    
    response = client.post(
        "/api/stores/1/staff",
        json={"phone": "0987654324", "full_name": "Nguyen Van D", "role": "MANAGER"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "Role SUPER_ADMIN cannot assign MANAGER" in response.json()["detail"]
