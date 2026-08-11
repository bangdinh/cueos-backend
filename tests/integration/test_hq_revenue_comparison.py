import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from database.database import init_db, SessionLocal
from database.models import PlaySession, BilliardTable, StoreModel
from api.auth import create_access_token

class TestHQRevenueComparisonTDD:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_hq_revenue_comparison_sorted_descending(self):
        """Tạo dữ liệu cho 3 chi nhánh với doanh thu khác nhau, xác nhận endpoint trả về đúng thứ tự và số liệu."""
        with TestClient(app) as client:
            db = SessionLocal()
            for sid, name in [(1, "Quán 1"), (2, "Quán 2"), (3, "Quán 3")]:
                st = db.query(StoreModel).filter(StoreModel.id == sid).first() or StoreModel(id=sid, name=name)
                db.merge(st)
                tb = db.query(BilliardTable).filter(BilliardTable.id == sid+200).first() or BilliardTable(id=sid+200, store_id=sid, name=f"T_{sid}", table_type="POOL", price_per_hour=50000)
                db.merge(tb)

            # Store 1: 100k, Store 2: 500k, Store 3: 300k
            s1 = PlaySession(table_id=201, store_id=1, status="COMPLETED", start_time=datetime.now(), end_time=datetime.now(), total_amount=100000, play_fee=100000, is_synced_to_hq=True)
            s2 = PlaySession(table_id=202, store_id=2, status="COMPLETED", start_time=datetime.now(), end_time=datetime.now(), total_amount=500000, play_fee=500000, is_synced_to_hq=True)
            s3 = PlaySession(table_id=203, store_id=3, status="COMPLETED", start_time=datetime.now(), end_time=datetime.now(), total_amount=300000, play_fee=300000, is_synced_to_hq=True)
            db.add_all([s1, s2, s3])
            db.commit()
            db.close()

            # Token SUPER_ADMIN
            admin_token = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "username": "admin"})
            headers = {"Authorization": f"Bearer {admin_token}"}

            resp = client.get("/api/hq/revenue-comparison", headers=headers)
            assert resp.status_code == 200
            res_json = resp.json()
            assert res_json.get("status") == "ok"
            data = res_json.get("data", [])
            assert len(data) >= 3

            # Lọc ra 3 store vừa test và kiểm tra thứ tự doanh thu giảm dần
            stores_dict = {item["store_id"]: item["total_revenue"] for item in data}
            assert stores_dict.get(2) >= 500000
            assert stores_dict.get(3) >= 300000
            assert stores_dict.get(1) >= 100000

            # Kiểm tra thứ tự giảm dần trong danh sách trả về
            revs = [item["total_revenue"] for item in data]
            assert revs == sorted(revs, reverse=True)

    def test_store_manager_cannot_access_revenue_comparison(self):
        """STORE_MANAGER cố tình gọi endpoint so sánh doanh thu HQ -> Bị từ chối 403."""
        with TestClient(app) as client:
            mgr_token = create_access_token({"user_id": 2, "store_id": 1, "role": "STORE_MANAGER", "username": "mgr1"})
            headers = {"Authorization": f"Bearer {mgr_token}"}

            resp = client.get("/api/hq/revenue-comparison", headers=headers)
            assert resp.status_code == 403
