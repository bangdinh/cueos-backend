import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from microservices.customer_service.main import app
from microservices.customer_service.database import get_db
from database.models.base import Base
from database.models.customer import CustomerModel
from microservices.billing_service.services.customer_service import CustomerService

# In-memory test DB
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

def test_create_and_get_customer():
    # 1. Tạo customer mới qua POST /api/customers
    payload = {
        "name": "Nguyễn Văn A",
        "phone": "0912345678",
        "store_id": 1,
        "points": 50
    }
    res = client.post("/api/customers", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Nguyễn Văn A"
    assert data["phone"] == "0912345678"
    assert data["store_id"] == 1
    assert data["points"] == 50
    customer_id = data["id"]

    # 2. Lấy thông tin theo ID qua GET /api/customers/{id}
    get_res = client.get(f"/api/customers/{customer_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Nguyễn Văn A"

def test_create_duplicate_phone_fails():
    client.post("/api/customers", json={"name": "Khách 1", "phone": "0900000001"})
    res2 = client.post("/api/customers", json={"name": "Khách 2", "phone": "0900000001"})
    assert res2.status_code == 400
    assert "đã tồn tại" in res2.json()["detail"]

def test_list_customers_by_store_and_phone():
    client.post("/api/customers", json={"name": "Khách Store 1", "phone": "0900000010", "store_id": 1})
    client.post("/api/customers", json={"name": "Khách Store 2", "phone": "0900000020", "store_id": 2})

    # Lọc theo store_id=1
    res_store1 = client.get("/api/customers?store_id=1")
    assert res_store1.status_code == 200
    assert len(res_store1.json()) == 1
    assert res_store1.json()[0]["phone"] == "0900000010"

    # Lọc theo phone
    res_phone = client.get("/api/customers?phone=0900000020")
    assert res_phone.status_code == 200
    assert len(res_phone.json()) == 1
    assert res_phone.json()[0]["name"] == "Khách Store 2"

def test_update_customer():
    create_res = client.post("/api/customers", json={"name": "Khách Cũ", "phone": "0933333333", "store_id": 1})
    cust_id = create_res.json()["id"]

    # Update tên và store_id
    update_res = client.put(f"/api/customers/{cust_id}", json={"name": "Khách Mới", "store_id": 2})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Khách Mới"
    assert update_res.json()["store_id"] == 2

def test_add_and_deduct_points():
    create_res = client.post("/api/customers", json={"name": "Khách VIP", "phone": "0977777777", "points": 100})
    cust_id = create_res.json()["id"]

    # Cộng 50 điểm
    add_res = client.put(f"/api/customers/{cust_id}/points", json={"points_delta": 50, "reason": "Chơi bida 2 tiếng"})
    assert add_res.status_code == 200
    assert add_res.json()["current_points"] == 150

    # Trừ 30 điểm
    sub_res = client.put(f"/api/customers/{cust_id}/points", json={"points_delta": -30, "reason": "Đổi voucher"})
    assert sub_res.status_code == 200
    assert sub_res.json()["current_points"] == 120

    # Trừ quá số điểm hiện có -> sàn về 0
    sub_all = client.put(f"/api/customers/{cust_id}/points", json={"points_delta": -200})
    assert sub_all.status_code == 200
    assert sub_all.json()["current_points"] == 0

@patch("requests.put")
def test_billing_service_http_client_add_points(mock_put):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "success", "customer_id": 1, "current_points": 250}
    mock_put.return_value = mock_resp

    result = CustomerService.add_points(customer_id=1, points=50, reason="Hóa đơn #123")
    assert result is not None
    assert result["current_points"] == 250
    mock_put.assert_called_once()
