import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from database.database import init_db, SessionLocal
from database.models import PlaySession, BilliardTable, StoreModel
from api.auth import create_access_token

class TestReportsByStoreTDD:
    @classmethod
    def setup_class(cls):
        init_db()

    def test_super_admin_can_filter_report_by_store(self):
        """SUPER_ADMIN xuất báo cáo store_id=2 -> chỉ nhận doanh thu của store 2."""
        with TestClient(app) as client:
            db = SessionLocal()
            # Seed 2 stores and sessions
            s1 = db.query(StoreModel).filter(StoreModel.id == 1).first() or StoreModel(id=1, name="Store 1")
            s2 = db.query(StoreModel).filter(StoreModel.id == 2).first() or StoreModel(id=2, name="Store 2")
            db.merge(s1)
            db.merge(s2)

            t1 = db.query(BilliardTable).filter(BilliardTable.id == 101).first() or BilliardTable(id=101, store_id=1, name="T1", table_type="POOL", price_per_hour=50000)
            t2 = db.query(BilliardTable).filter(BilliardTable.id == 102).first() or BilliardTable(id=102, store_id=2, name="T2", table_type="POOL", price_per_hour=50000)
            db.merge(t1)
            db.merge(t2)

            sess1 = PlaySession(table_id=101, store_id=1, status="COMPLETED", start_time=datetime.now(), end_time=datetime.now(), total_amount=100000, play_fee=100000)
            sess2 = PlaySession(table_id=102, store_id=2, status="COMPLETED", start_time=datetime.now(), end_time=datetime.now(), total_amount=250000, play_fee=250000)
            db.add_all([sess1, sess2])
            db.commit()
            db.close()

            # Token SUPER_ADMIN
            admin_token = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "username": "admin"})
            headers = {"Authorization": f"Bearer {admin_token}"}

            # Lọc store_id=2
            resp = client.get("/api/reports/revenue?store_id=2", headers=headers)
            assert resp.status_code == 200
            content = resp.text
            assert "T2" in content
            assert "T1" not in content

    def test_store_manager_forced_to_own_store_in_report(self):
        """MANAGER của store 1 cố truyền store_id=2 -> vẫn bị ép về store 1."""
        with TestClient(app) as client:
            mgr_token = create_access_token({"user_id": 2, "store_id": 1, "role": "MANAGER", "username": "mgr1"})
            headers = {"Authorization": f"Bearer {mgr_token}"}

            # Cố tình truyền store_id=2
            resp = client.get("/api/reports/revenue?store_id=2", headers=headers)
            assert resp.status_code == 200
            content = resp.text
            assert "T1" in content
            assert "T2" not in content
