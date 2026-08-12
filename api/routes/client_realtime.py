import json
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import redis as redis_lib
from api.websocket_server import websocket_manager
import hashlib

SECRET_KEY = "BIDA_AI_SECURE_KEY_2026"
def generate_table_token(table_id: int) -> str:
    return hashlib.md5(f"{SECRET_KEY}_{table_id}".encode()).hexdigest()[:8]

client_messages_store = {}
router = APIRouter(prefix="/api", tags=["Client Realtime"])

@router.post("/client-notify/{table_id}")
def notify_client(table_id: int, payload: dict):
    message = payload.get("message", "")
    msg_type = payload.get("type", "info")
    redirect_url = payload.get("redirect_url", "")
    
    data = {
        "message": message,
        "type": msg_type,
        "redirect_url": redirect_url,
        "timestamp": time.time()
    }
    client_messages_store[table_id] = data
    try:
        r = redis_lib.Redis(host='127.0.0.1', port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        r.set(f"client_msg_{table_id}", json.dumps(data))
        r.expire(f"client_msg_{table_id}", 300)
    except Exception:
        pass
    return JSONResponse({"status": "ok"})

@router.get("/client-poll/{table_id}")
def poll_client(table_id: int):
    data = None
    if table_id in client_messages_store:
        data = client_messages_store.pop(table_id)
    try:
        r = redis_lib.Redis(host='127.0.0.1', port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        if data:
            r.delete(f"client_msg_{table_id}")
        else:
            msg = r.get(f"client_msg_{table_id}")
            if msg:
                r.delete(f"client_msg_{table_id}")
                data = json.loads(msg)
    except Exception:
        pass
        
    if data:
        return JSONResponse({"has_message": True, "data": data})
    return JSONResponse({"has_message": False})

from api.middleware.store_context import StoreContext, get_store_context
from fastapi import Depends

@router.get("/poll")
def poll_events(ctx: StoreContext = Depends(get_store_context)):
    try:
        if websocket_manager.latest_payload and websocket_manager.latest_payload != "{}":
            data = json.loads(websocket_manager.latest_payload)
            events = [data] if data else []
        else:
            events = []
            
        if not ctx.is_hq and events:
            # Lọc event theo store_id
            events = [e for e in events if e.get("store_id") == ctx.store_id]
    except Exception:
        events = []
    return JSONResponse({"status": "ok", "events": events})

from database.models import StaffNotification
from fastapi import HTTPException
from database.database import SessionLocal

@router.post("/notifications/{notif_id}/resolve")
def resolve_notification(notif_id: int, ctx: StoreContext = Depends(get_store_context)):
    if ctx.is_hq:
        raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc")
    
    db = SessionLocal()
    try:
        notif = db.query(StaffNotification).filter(StaffNotification.id == notif_id).first()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
        if notif.store_id != ctx.store_id:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập cửa hàng này")
            
        notif.status = "RESOLVED"
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()
