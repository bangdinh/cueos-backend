import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import init_db, SessionLocal
from database.models import StaffNotification
from api.auth import create_access_token

class TestHQCannotConfirmServiceTDD:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_hq_cannot_confirm_service_returns_403(self):
        """Giả lập SUPER_ADMIN gọi API xác nhận phục vụ -> phải nhận 403."""
        with TestClient(app) as client:
            # Tạo staff notification trong DB
            db = SessionLocal()
            notif = StaffNotification(table_id=1, store_id=1, notification_type="ORDER_FOOD", status="PENDING")
            db.add(notif)
            db.commit()
            db.refresh(notif)
            notif_id = notif.id
            db.close()

            # Tạo token SUPER_ADMIN
            admin_token = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "username": "admin"})
            headers = {"Authorization": f"Bearer {admin_token}"}

            # SUPER_ADMIN cố tình gọi API xác nhận đã phục vụ
            resp = client.post(f"/api/notifications/{notif_id}/resolve", headers=headers)
            assert resp.status_code == 403
            assert "máy mẹ" in resp.text.lower() or "chỉ có quyền đọc" in resp.text.lower() or "read-only" in resp.text.lower()

            # Kiểm tra trong DB trạng thái notif vẫn là PENDING
            db = SessionLocal()
            saved_notif = db.query(StaffNotification).filter(StaffNotification.id == notif_id).first()
            assert saved_notif.status == "PENDING"
            db.close()

            # MANAGER gọi xác nhận phục vụ -> phải thành công (200)
            mgr_token = create_access_token({"user_id": 2, "store_id": 1, "role": "MANAGER", "username": "mgr1"})
            mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
            resp_mgr = client.post(f"/api/notifications/{notif_id}/resolve", headers=mgr_headers)
            assert resp_mgr.status_code == 200

            db = SessionLocal()
            saved_notif2 = db.query(StaffNotification).filter(StaffNotification.id == notif_id).first()
            assert saved_notif2.status == "RESOLVED"
            db.delete(saved_notif2)
            db.commit()
            db.close()
