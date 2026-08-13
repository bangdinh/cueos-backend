import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, BilliardTable, Product, PlaySession, AIEvent
import database.crud as crud

from sqlalchemy.pool import StaticPool

# Chuẩn bị SQLite in-memory cho testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    from database.seed import seed_default_store_and_users
    seed_default_store_and_users(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

class TestStoreDataIsolationCRUDTDD:
    """
    TDD Phase 3 (RED): Integration test kiểm chứng sự cách ly dữ liệu giữa các cửa hàng ở tầng CRUD SQL.
    """

    def test_table_crud_tenant_isolation(self, db_session):
        """Test bảng billiard_tables phải được cách ly hoàn toàn theo store_id."""
        from database.models import StoreModel
        
        # 1. Tạo 2 store
        store1 = StoreModel(id=1, name="Quán Quận 1")
        store2 = StoreModel(id=2, name="Quán Quận 7")
        db_session.merge(store1)
        db_session.merge(store2)
        db_session.commit()
        
        # 2. Thêm bàn vào store 1 và store 2
        t1 = BilliardTable(name="Bàn Q1 - 01", store_id=1, price_per_hour=50000.0)
        t2 = BilliardTable(name="Bàn Q7 - 01", store_id=2, price_per_hour=70000.0)
        db_session.add_all([t1, t2])
        db_session.commit()
        
        # 3. Quán 1 query chỉ thấy bàn của quán 1
        tables_s1 = crud.get_active_tables(db_session, store_id=1)
        assert len(tables_s1) == 1
        assert tables_s1[0].name == "Bàn Q1 - 01"
        assert tables_s1[0].store_id == 1
        
        # 4. Quán 2 query chỉ thấy bàn của quán 2
        tables_s2 = crud.get_active_tables(db_session, store_id=2)
        assert len(tables_s2) == 1
        assert tables_s2[0].name == "Bàn Q7 - 01"
        assert tables_s2[0].store_id == 2
        
        # 5. Máy Mẹ (HQ - SUPER_ADMIN) query hàm tổng hợp thấy tất cả bàn của 2 quán
        all_tables_hq = crud.get_hq_all_tables(db_session)
        assert len(all_tables_hq) == 2

    def test_product_and_session_crud_tenant_isolation(self, db_session):
        """Test bảng products và play_sessions phải cách ly theo store_id và có cờ is_synced_to_hq."""
        from database.models import StoreModel, SessionOrderItem
        
        store1 = StoreModel(id=1, name="Quán Quận 1")
        store2 = StoreModel(id=2, name="Quán Quận 7")
        db_session.merge(store1)
        db_session.merge(store2)
        db_session.commit()
        
        # Thêm product vào store 1 và store 2
        p1 = Product(name="Sting Q1", price=15000, store_id=1)
        p2 = Product(name="Sting Q7", price=18000, store_id=2)
        db_session.add_all([p1, p2])
        db_session.commit()
        
        products_s1 = crud.get_products_by_store(db_session, store_id=1)
        assert len(products_s1) == 1
        assert products_s1[0].name == "Sting Q1"
        
        # Thêm session vào store 1
        sess1 = PlaySession(table_id=1, store_id=1, status="COMPLETED", total_amount=100000.0, is_synced_to_hq=False)
        db_session.add(sess1)
        db_session.commit()
        
        # Denormalized store_id trong session_order_items
        order_item1 = SessionOrderItem(session_id=sess1.id, store_id=1, item_name="Sting Q1", quantity=2, price=15000, total_price=30000)
        db_session.add(order_item1)
        db_session.commit()
        
        # Kiểm tra truy vấn doanh thu chưa sync của store 1
        unsynced = crud.get_unsynced_completed_sessions(db_session, store_id=1)
        assert len(unsynced) == 1
        assert unsynced[0].is_synced_to_hq is False
        assert unsynced[0].store_id == 1
        
        # Quán 2 không nhìn thấy session của quán 1
        unsynced_s2 = crud.get_unsynced_completed_sessions(db_session, store_id=2)
        assert len(unsynced_s2) == 0

    def test_api_routes_tenant_isolation_and_hq_readonly(self):
        """Test middleware get_store_context phân lập dữ liệu theo token và chặn HQ ghi dữ liệu."""
        from fastapi.testclient import TestClient
        from main import app
        from database.database import init_db
        from api.auth import create_access_token
        from database.database import get_db

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        app.dependency_overrides[get_db] = override_get_db
        init_db()
        
        token_hq = create_access_token({"user_id": 1, "role": "SUPER_ADMIN", "store_id": None})
        token_s1 = create_access_token({"user_id": 2, "role": "MANAGER", "store_id": 1})
        
        with TestClient(app) as client:
            # 1. Trụ sở Máy Mẹ (SUPER_ADMIN) cố tình gọi API tạo bàn -> Bị từ chối 403 Forbidden
            resp_hq_write = client.post("/api/admin/tables/add", json={
                "name": "Bàn HQ Tạo Trộm",
                "table_type": "LIP",
                "price_per_hour": 50000
            }, headers={"Authorization": f"Bearer {token_hq}"})
            assert resp_hq_write.status_code == 403
            assert "chỉ có quyền đọc" in resp_hq_write.text
            
            # 2. Khách hàng/nhân viên Quán 1 gọi API list tables
            resp_s1 = client.get("/api/tables", headers={"Authorization": f"Bearer {token_s1}"})
            assert resp_s1.status_code == 200
            for table in resp_s1.json():
                assert table.get("store_id", 1) == 1

    def test_websocket_and_pubsub_realtime_isolation(self):
        """Test ConnectionManager phát realtime đúng chi nhánh và HQ nhận tất cả."""
        import pytest
        import asyncio
        from api.websocket_server import ConnectionManager
        
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            async def accept(self):
                pass
            async def send_text(self, message: str):
                self.messages.append(message)
                
        manager = ConnectionManager()
        ws_s1 = MockWebSocket()
        ws_s2 = MockWebSocket()
        ws_hq = MockWebSocket()
        
        async def run_test():
            await manager.connect(ws_s1, store_id=1)
            await manager.connect(ws_s2, store_id=2)
            await manager.connect(ws_hq, is_hq=True)
            
            # Broadcast cho store 1
            await manager.broadcast("Event Store 1", store_id=1)
            assert "Event Store 1" in ws_s1.messages
            assert "Event Store 1" in ws_hq.messages
            assert "Event Store 1" not in ws_s2.messages
            
            # Broadcast cho store 2
            await manager.broadcast("Event Store 2", store_id=2)
            assert "Event Store 2" in ws_s2.messages
            assert "Event Store 2" in ws_hq.messages
            assert "Event Store 2" not in ws_s1.messages
            
        asyncio.run(run_test())

    def test_poll_endpoint_store_isolation_and_admin_login(self, db_session):
        from fastapi.testclient import TestClient
        from main import app
        from database.database import get_db

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            # 1. Test đăng nhập admin với whitespace và case-insensitive
            r_admin = client.post("/api/auth/login", json={"username": " ADMIN ", "password": " secret "})
            assert r_admin.status_code == 200
            token_admin = r_admin.json()["access_token"]

            # 2. Test đăng nhập quản lý store 1 & store 2
            r_mgr1 = client.post("/api/auth/login", json={"username": "manager1", "password": "secret"})
            token_mgr1 = r_mgr1.json()["access_token"]
            r_mgr2 = client.post("/api/auth/login", json={"username": "manager2", "password": "secret"})
            token_mgr2 = r_mgr2.json()["access_token"]

            # 3. Giả lập websocket_manager có event từ store 1
            from api.websocket_server import websocket_manager
            import json
            websocket_manager.latest_payload = json.dumps({"event_type": "NEW_ORDER", "store_id": 1, "message": "Store 1 Order"})

            # Quán 1 thấy event
            r_poll1 = client.get("/api/poll", headers={"Authorization": f"Bearer {token_mgr1}"})
            assert r_poll1.status_code == 200
            assert len(r_poll1.json()["events"]) == 1
            assert r_poll1.json()["events"][0]["store_id"] == 1

            # Quán 2 KHÔNG thấy event của Quán 1 (isolation)
            r_poll2 = client.get("/api/poll", headers={"Authorization": f"Bearer {token_mgr2}"})
            assert r_poll2.status_code == 200
            assert len(r_poll2.json()["events"]) == 0

            # HQ (Admin) thấy toàn bộ event
            r_poll_hq = client.get("/api/poll", headers={"Authorization": f"Bearer {token_admin}"})
            assert r_poll_hq.status_code == 200
            assert len(r_poll_hq.json()["events"]) == 1

        app.dependency_overrides.clear()
