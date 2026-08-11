import os
import json
import time
import math
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import redis as redis_lib

from ..database import SessionLocal
from ..models.session import PlaySession
from ..models.billiard_table import BilliardTable

# Token generator helper
import hashlib
SECRET_KEY = "BIDA_AI_SECURE_KEY_2026"
def generate_table_token(table_id: int) -> str:
    return hashlib.md5(f"{SECRET_KEY}_{table_id}".encode()).hexdigest()[:8]

def broadcast_to_websocket(event_data: dict, store_id: int):
    try:
        r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        event_data['store_id'] = store_id
        r.publish('ws_broadcast_events', json.dumps(event_data))
    except Exception as e:
        print(f"Failed to publish to redis: {e}")

class StoreContext:
    def __init__(self, store_id: int, role: str):
        self.store_id = store_id
        self.role = role
    def require_write_permission(self):
        pass
    def require_admin_permission(self):
        pass

def get_store_context():
    return StoreContext(store_id=1, role="STORE_MANAGER")

router = APIRouter(prefix="/api", tags=["Sessions"])

@router.get("/session/active/{table_id}")
def get_active_session(table_id: int):
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table or table.current_status != "PLAYING":
            return JSONResponse({"status": "error"}, status_code=404)
            
        session = db.query(PlaySession).filter(PlaySession.table_id == table_id, PlaySession.status == "ACTIVE").first()
        if session:
            return {"id": session.id, "store_id": session.store_id}
        return JSONResponse({"status": "error"}, status_code=404)
    finally:
        db.close()

@router.post("/session/start/{table_id}")
def start_session(table_id: int, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Khong tim thay ban"}, status_code=404)
        if table.current_status == "PLAYING":
            return JSONResponse({"status": "error", "message": "Ban dang choi roi"}, status_code=400)
            
        table.current_status = "PLAYING"
        new_session = PlaySession(table_id=table_id, store_id=table.store_id)
        db.add(new_session)
        db.commit()

        event_data = {"event": "SESSION_STARTED", "table_id": table_id, "store_id": table.store_id}
        broadcast_to_websocket(event_data, table.store_id)

        return JSONResponse({"status": "ok", "message": "Da bat dau tinh gio ban", "session_id": new_session.id})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.post("/session/stop/{table_id}")
def stop_session(table_id: int, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Khong tim thay ban"}, status_code=404)
        if table.current_status != "PLAYING":
            return JSONResponse({"status": "error", "message": "Ban chua bat tinh gio"}, status_code=400)
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        if not active_session:
            return JSONResponse({"status": "error", "message": "Khong tim thay phien choi active"}, status_code=400)
            
        end_time = datetime.utcnow()
        duration = end_time - active_session.start_time
        total_minutes = max(1, math.ceil(duration.total_seconds() / 60))
        
        play_fee = math.ceil((total_minutes / 60.0) * table.price_per_hour)
        
        
        # Call Order Service to get items
        service_total = 0
        items_data = []
        try:
            # Synchronous call for simplicity, but better use async httpx
            with httpx.Client() as client:
                resp = client.get(f"{os.environ.get('ORDER_SERVICE_URL', 'http://127.0.0.1:8005')}/api/orders/{active_session.id}")
                if resp.status_code == 200:
                    data = resp.json()
                    items_data = data.get("items", [])
                    service_total = sum(i["total_price"] for i in items_data)
        except Exception as e:
            print(f"Failed to fetch orders from Order Service: {e}")
            
        total_bill = play_fee + service_total
        
        active_session.end_time = end_time
        active_session.total_minutes = total_minutes
        active_session.play_fee = play_fee
        active_session.services_fee = service_total
        active_session.total_amount = total_bill
        active_session.store_id = table.store_id
        active_session.status = "COMPLETED"
        
        table.current_status = "EMPTY"
        db.commit()

        event_data = {"event": "SESSION_COMPLETED", "table_id": table_id, "store_id": table.store_id, "total_amount": total_bill}
        broadcast_to_websocket(event_data, table.store_id)
        
        return JSONResponse({
            "status": "ok",
            "message": "Da thanh toan phien choi",
            "bill": {
                "session_id": active_session.id,
                "table_name": table.name,
                "start_time": active_session.start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "total_minutes": total_minutes,
                "play_fee": play_fee,
                "service_total": service_total,
                "total_bill": total_bill,
                "items": items_data

            }
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.post("/session/transfer/{from_table_id}/{to_table_id}")
def transfer_session(from_table_id: int, to_table_id: int, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    db = SessionLocal()
    try:
        if from_table_id == to_table_id:
            return JSONResponse({"status": "error", "message": "Không thể chuyển sang cùng bàn!"}, status_code=400)
            
        from_table = db.query(BilliardTable).filter(BilliardTable.id == from_table_id).first()
        to_table = db.query(BilliardTable).filter(BilliardTable.id == to_table_id).first()
        
        if not from_table or not to_table:
            return JSONResponse({"status": "error", "message": "Bàn không tồn tại!"}, status_code=404)
            
        if from_table.current_status != "PLAYING":
            return JSONResponse({"status": "error", "message": f"{from_table.name} không ở trạng thái đang chơi!"}, status_code=400)
            
        if to_table.current_status == "PLAYING":
            return JSONResponse({"status": "error", "message": f"{to_table.name} đã có khách chơi, không thể chuyển sang!"}, status_code=400)
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == from_table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            return JSONResponse({"status": "error", "message": "Không tìm thấy phiên chơi active!"}, status_code=404)
            
        active_session.table_id = to_table_id
        from_table.current_status = "EMPTY"
        to_table.current_status = "PLAYING"
        
        db.commit()

        to_token = generate_table_token(to_table_id)
        new_url = f"/menu/{to_table_id}/{to_token}"
        
        notify_data = {
            "message": f"Yêu cầu đổi bàn đã được chấp nhận! Bạn đã được chuyển từ {from_table.name} sang {to_table.name}.",
            "type": "redirect",
            "redirect_url": new_url,
            "timestamp": time.time(),
            "table_id": from_table_id
        }
        
        try:
            r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
            r.set(f"client_msg_{from_table_id}", json.dumps(notify_data))
            r.expire(f"client_msg_{from_table_id}", 300)
            
            # also broadcast event so monolith can know
            event_data = {"event": "SESSION_TRANSFERRED", "from_table_id": from_table_id, "to_table_id": to_table_id, "store_id": from_table.store_id}
            r.publish('ws_broadcast_events', json.dumps(event_data))
        except Exception:
            pass
            
        return JSONResponse({
            "status": "ok",
            "message": f"Đã chuyển phiên chơi thành công từ {from_table.name} sang {to_table.name}!"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.get("/history")
def get_history(store_id: int = None, ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        # For simplicity in extracted service, assuming role checking isn't strict yet
        target = store_id or ctx.store_id
        if target:
            sessions = db.query(PlaySession).filter(PlaySession.status == "COMPLETED", PlaySession.store_id == target).order_by(PlaySession.end_time.desc()).all()
        else:
            sessions = db.query(PlaySession).filter(PlaySession.status == "COMPLETED").order_by(PlaySession.end_time.desc()).all()
        
        result = []
        for s in sessions:
            table = db.query(BilliardTable).filter(BilliardTable.id == s.table_id).first()
            
            # In a real microservice, we would batch fetch this or store a snapshot in Session Service.
            # For now, we skip fetching items in history list to avoid N+1 queries to Order Service,
            # or just default to empty items. The total is already saved in s.services_fee.
            service_total = s.services_fee or 0
            total_bill = (s.play_fee or 0) + service_total
            
            can_delete = False
            if s.end_time:
                diff_hours = (now - s.end_time).total_seconds() / 3600.0
                if diff_hours <= 2.0:
                    can_delete = True
                    
            result.append({
                "id": s.id,
                "table_id": s.table_id,
                "table_name": table.name if table else f"Bàn {s.table_id}",
                "start_time": s.start_time.isoformat() + "Z",
                "end_time": s.end_time.isoformat() + "Z" if s.end_time else None,
                "total_minutes": s.total_minutes or 0,
                "play_fee": s.play_fee or 0,
                "service_total": service_total,
                "total_bill": total_bill,
                "can_delete": can_delete,
                "items": []

            })
        return JSONResponse(result)
    finally:
        db.close()

@router.delete("/history")
def delete_history(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    ids = payload.get("ids", [])
    if not ids:
        return JSONResponse({"status": "error", "message": "Không có hóa đơn nào được chọn"}, status_code=400)
        
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        deleted_count = 0
        cannot_delete_count = 0
        
        for hid in ids:
            session = db.query(PlaySession).filter(PlaySession.id == hid, PlaySession.status == "COMPLETED").first()
            if not session:
                continue
                
            if session.end_time:
                diff_hours = (now - session.end_time).total_seconds() / 3600.0
                if diff_hours > 2.0:
                    cannot_delete_count += 1
                    continue
                    
            # In real MS, we publish an event SESSION_DELETED so Order Service deletes items.
            db.delete(session)
            deleted_count += 1
            
        db.commit()
        
        msg = f"Đã xóa thành công {deleted_count} hóa đơn."
        if cannot_delete_count > 0:
            msg += f" (Bỏ qua {cannot_delete_count} hóa đơn đã quá 2 giờ)"
            
        return JSONResponse({"status": "ok", "message": msg})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()
