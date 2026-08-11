import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import init_db
from api.auth import create_access_token

class TestHQCannotModifyInventoryTDD:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_super_admin_add_table_without_store_id_returns_403(self):
        """SUPER_ADMIN cố gọi API thêm bàn mà không chọn store_id -> bị từ chối 403 Forbidden theo Hướng (a)."""
        with TestClient(app) as client:
            admin_token = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "username": "admin"})
            headers = {"Authorization": f"Bearer {admin_token}"}
            payload = {"name": "Bàn Test HQ", "table_type": "POOL", "price_per_hour": 50000}

            resp = client.post("/api/admin/tables/add", json=payload, headers=headers)
            assert resp.status_code == 403

    def test_super_admin_add_table_with_store_id_returns_403(self):
        """SUPER_ADMIN cố gọi API thêm bàn có chọn store_id -> bị từ chối 403 Forbidden theo hướng (a)."""
        with TestClient(app) as client:
            admin_token = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "username": "admin"})
            headers = {"Authorization": f"Bearer {admin_token}"}
            payload = {"name": "Bàn Test HQ", "table_type": "POOL", "price_per_hour": 50000, "store_id": 2}

            resp = client.post("/api/admin/tables/add", json=payload, headers=headers)
            assert resp.status_code == 403

    def test_super_admin_modify_products_returns_403(self):
        """SUPER_ADMIN cố gọi API thêm sản phẩm -> bị từ chối 403 Forbidden theo Hướng (a)."""
        with TestClient(app) as client:
            admin_token = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "username": "admin"})
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Không có store_id -> 403
            resp1 = client.post("/api/products/add", json={"name": "Bia HQ", "price": 20000, "stock": 10}, headers=headers)
            assert resp1.status_code == 403

            # Có store_id -> 403
            resp2 = client.post("/api/products/add", json={"name": "Bia HQ", "price": 20000, "stock": 10, "store_id": 2}, headers=headers)
            assert resp2.status_code == 403
