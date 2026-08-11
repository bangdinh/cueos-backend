import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import init_db

class TestForgedHeaderRejectedTDD:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_forged_headers_without_token_are_rejected(self):
        """Giả lập client tự gửi X-Store-ID và X-User-Role KHÔNG kèm token JWT hợp lệ -> Bị từ chối 401."""
        with TestClient(app) as client:
            # Client tự nhận là SUPER_ADMIN và cố tình gọi GET /api/tables
            headers = {
                "X-Store-ID": "1",
                "X-User-Role": "SUPER_ADMIN",
                "X-User-ID": "1"
            }
            resp = client.get("/api/tables", headers=headers)
            assert resp.status_code == 401
            assert any(w in resp.text.lower() for w in ["unauthorized", "authorization", "token", "authenticated", "credentials"])

    def test_forged_headers_with_invalid_token_are_rejected(self):
        """Giả lập client gửi header tự khai kèm token giả mạo -> Bị từ chối 401."""
        with TestClient(app) as client:
            headers = {
                "X-Store-ID": "1",
                "X-User-Role": "SUPER_ADMIN",
                "Authorization": "Bearer fake.jwt.token.string"
            }
            resp = client.get("/api/tables", headers=headers)
            assert resp.status_code == 401
