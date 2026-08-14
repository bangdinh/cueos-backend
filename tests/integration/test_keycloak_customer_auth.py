import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from microservices.customer_service.main import app
from microservices.customer_service.database import get_db
from microservices.customer_service.keycloak_auth import get_current_keycloak_user
from database.models.base import Base
from database.models.customer import CustomerModel

# Use SQLite in-memory with StaticPool so all connections share the same memory DB
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
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_keycloak_user, None)

def test_customer_me_auto_creates_customer_profile():
    # Mock Keycloak user with CUSTOMER role
    def mock_keycloak_customer():
        return {
            "sub": "kc-user-uuid-12345",
            "preferred_username": "khachhang1",
            "email": "khachhang1@bida.vn",
            "realm_access": {
                "roles": ["CUSTOMER", "default-roles-bida-realm"]
            }
        }
    
    app.dependency_overrides[get_current_keycloak_user] = mock_keycloak_customer
    
    # 1. Gọi API /api/customer/me
    response = client.get("/api/customer/me")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["username"] == "khachhang1"
    assert data["points"] == 0
    assert data["keycloak_sub"] == "kc-user-uuid-12345"

    # 2. Kiểm tra dữ liệu được tạo trong auth.db
    db = TestingSessionLocal()
    customer_db = db.query(CustomerModel).filter(CustomerModel.name == "khachhang1").first()
    assert customer_db is not None
    assert customer_db.points == 0
    db.close()

def test_customer_update_profile_and_points():
    def mock_keycloak_customer():
        return {
            "sub": "kc-user-uuid-12345",
            "preferred_username": "khachhang1",
            "email": "khachhang1@bida.vn",
            "realm_access": {
                "roles": ["CUSTOMER"]
            }
        }
    app.dependency_overrides[get_current_keycloak_user] = mock_keycloak_customer

    # Cập nhật số điện thoại
    response = client.put("/api/customer/profile", json={"phone": "0988888888", "store_id": 1})
    assert response.status_code == 200
    assert response.json()["customer"]["phone"] == "0988888888"

    # Kiểm tra điểm thưởng
    points_res = client.get("/api/customer/points")
    assert points_res.status_code == 200
    assert points_res.json()["tier"] == "BRONZE"

def test_customer_forbidden_when_role_missing():
    # User chỉ có role STAFF mà không có role CUSTOMER
    def mock_keycloak_staff():
        return {
            "sub": "kc-staff-uuid",
            "preferred_username": "nhanvien1",
            "realm_access": {
                "roles": ["STAFF"]
            }
        }
    app.dependency_overrides[get_current_keycloak_user] = mock_keycloak_staff

    response = client.get("/api/customer/me")
    assert response.status_code == 403
    assert "CUSTOMER" in response.json()["detail"]
