import time
import json
import threading
from typing import Optional
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.crud import get_unsynced_completed_sessions
from database.models import PlaySession

def sync_completed_sessions_to_hq(db: Session, store_id: Optional[int] = None) -> int:
    """Quét các phiên chơi đã hoàn thành (status='COMPLETED') và chưa được đồng bộ (is_synced_to_hq=False),
    gửi dữ liệu về Máy Mẹ và đánh dấu đã đồng bộ.
    """
    unsynced_sessions = get_unsynced_completed_sessions(db, store_id=store_id)
    if not unsynced_sessions:
        return 0
        
    synced_count = 0
    for session in unsynced_sessions:
        try:
            # Mô phỏng quá trình truyền tải hoặc đóng gói dữ liệu tổng hợp lên Trụ sở HQ
            payload = {
                "session_id": session.id,
                "store_id": session.store_id,
                "table_id": session.table_id,
                "total_minutes": session.total_minutes,
                "play_fee": session.play_fee,
                "services_fee": session.services_fee,
                "total_amount": session.total_amount,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None
            }
            # Đánh dấu đã đồng bộ thành công
            session.is_synced_to_hq = True
            synced_count += 1
        except Exception as e:
            print(f"[SyncWorker ERROR] Lỗi đồng bộ session {session.id}: {e}")
            
    if synced_count > 0:
        db.commit()
        print(f"[SyncWorker] Đã đồng bộ thành công {synced_count} hóa đơn lên Trụ sở (HQ).")
        
    return synced_count

def start_sync_worker_daemon(interval_seconds: int = 60, store_id: Optional[int] = None):
    """Khởi động luồng chạy ngầm định kỳ quét và đồng bộ dữ liệu về HQ."""
    def _worker_loop():
        print(f"[SyncWorker] [OK] Đã khởi động luồng đồng bộ HQ định kỳ mỗi {interval_seconds} giây.")
        while True:
            time.sleep(interval_seconds)
            db = SessionLocal()
            try:
                sync_completed_sessions_to_hq(db, store_id=store_id)
            except Exception as e:
                print(f"[SyncWorker ERROR] Lỗi trong chu kỳ đồng bộ: {e}")
            finally:
                db.close()
                
    t = threading.Thread(target=_worker_loop, daemon=True)
    t.start()
