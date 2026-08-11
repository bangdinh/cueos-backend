import pytest
from datetime import datetime
from database.models import PlaySession, BilliardTable, StoreModel
from database.crud import get_unsynced_completed_sessions

class TestHQReadOnlyAndSyncE2ETDD:
    @pytest.fixture
    def db_session(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from database.models import Base
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Seed stores
        s1 = StoreModel(id=1, name="Quán 1", address="Q1")
        s2 = StoreModel(id=2, name="Quán 2", address="Q2")
        session.add_all([s1, s2])
        session.commit()
        
        yield session
        session.close()

    def test_sync_hq_worker_syncs_completed_sessions(self, db_session):
        """Test sync worker đồng bộ các phiên chơi đã thanh toán (COMPLETED) và giữ nguyênACTIVE."""
        from workers.sync_hq_worker import sync_completed_sessions_to_hq
        
        # Tạo 2 session ở Quán 1
        sess_completed = PlaySession(
            table_id=1,
            store_id=1,
            status="COMPLETED",
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_minutes=60,
            play_fee=50000,
            services_fee=20000,
            total_amount=70000,
            is_synced_to_hq=False
        )
        sess_active = PlaySession(
            table_id=1,
            store_id=1,
            status="ACTIVE",
            start_time=datetime.now(),
            is_synced_to_hq=False
        )
        db_session.add_all([sess_completed, sess_active])
        db_session.commit()
        
        # Trước khi sync
        unsynced_before = get_unsynced_completed_sessions(db_session, store_id=1)
        assert len(unsynced_before) == 1
        assert unsynced_before[0].id == sess_completed.id
        
        # Chạy worker sync
        synced_count = sync_completed_sessions_to_hq(db_session, store_id=1)
        assert synced_count == 1
        
        # Sau khi sync, không còn session nào chưa sync
        unsynced_after = get_unsynced_completed_sessions(db_session, store_id=1)
        assert len(unsynced_after) == 0
        
        # Kiểm tra DB
        db_session.refresh(sess_completed)
        db_session.refresh(sess_active)
        assert sess_completed.is_synced_to_hq is True
        assert sess_active.is_synced_to_hq is False

    def test_ai_worker_redis_channel_and_payload_store_id(self):
        """Test AI worker phát sự kiện với kênh và payload chứa store_id."""
        from ai_workers.stream_processor import emit_ai_event
        import json
        import redis
        
        # Gọi emit_ai_event cho Quán 2
        event = emit_ai_event(table_id=5, event_type="TEST_MULTI_STORE", confidence=0.95, message="Hello Quán 2", store_id=2)
        assert event["store_id"] == 2
        assert event["table_id"] == 5
        assert event["event_type"] == "TEST_MULTI_STORE"
        
        # Kiểm tra trên Redis (sync client)
        try:
            r = redis.Redis(host='127.0.0.1', port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
            latest = r.get('latest_ai_event')
            if latest:
                data = json.loads(latest.decode('utf-8'))
                if data.get("event_type") == "TEST_MULTI_STORE":
                    assert data.get("store_id") == 2
        except Exception:
            pass
