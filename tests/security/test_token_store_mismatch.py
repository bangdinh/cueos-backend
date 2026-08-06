import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import init_db
from datetime import timedelta

class TestTokenStoreMismatchTDD:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_store_manager_token_ignores_forged_store_id_header(self):
        """User có token hợp lệ của Quán 1 cố tình gửi X-Store-ID: 2 -> Phải chỉ trả về dữ liệu Quán 1."""
        from api.auth import create_access_token
        
        token_store_1 = create_access_token(
            {"user_id": 2, "store_id": 1, "role": "STORE_MANAGER"},
            expires_delta=timedelta(hours=1)
        )
        
        with TestClient(app) as client:
            headers = {
                "Authorization": f"Bearer {token_store_1}",
                "X-Store-ID": "2"  # Cố tình mạo danh quán 2
            }
            resp = client.get("/api/tables", headers=headers)
            assert resp.status_code == 200
            tables = resp.json()
            assert len(tables) > 0
            for table in tables:
                assert table.get("store_id", 1) == 1  # Luôn phải là 1, bỏ qua X-Store-ID: 2

    def test_cashier_token_cannot_access_other_store(self):
        """Cashier có token của Quán 1 gửi request với X-Store-ID: 2 -> Dữ liệu trả về hoặc thao tác luôn thuộc Quán 1."""
        from api.auth import create_access_token
        
        token_cashier_1 = create_access_token(
            {"user_id": 3, "store_id": 1, "role": "CASHIER"},
            expires_delta=timedelta(hours=1)
        )
        
        with TestClient(app) as client:
            headers = {
                "Authorization": f"Bearer {token_cashier_1}",
                "X-Store-ID": "2"
            }
            resp = client.get("/api/inventory", headers=headers)
            assert resp.status_code == 200
            # Dữ liệu trả về phải của chi nhánh 1 theo token, không lỗi và không rò rỉ của quán 2
