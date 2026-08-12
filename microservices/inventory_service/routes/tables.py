import os
import json
import csv
import io
import time
import re
import math
from datetime import datetime
from fastapi import APIRouter, Response, Depends
from ..middleware.store_context import StoreContext, get_store_context
from fastapi import Depends
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
import redis as redis_lib
from ..database import SessionLocal
from database.models.billiard_table import BilliardTable
from database.models.product import Product
# WS disabled

# Token generator helper
import hashlib
SECRET_KEY = "BIDA_AI_SECURE_KEY_2026"
def generate_table_token(table_id: int) -> str:
    return hashlib.md5(f"{SECRET_KEY}_{table_id}".encode()).hexdigest()[:8]

CLIPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "clips")
client_messages_store = {}

router = APIRouter(prefix="/api", tags=["Tables"])

@router.get("/tables")
def list_tables(store_id: int = None, ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        target = store_id if (ctx.role.value == 'SUPER_ADMIN' and store_id) else ctx.store_id
        if target:
            tables = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.store_id == target).order_by(BilliardTable.id).all()
        else:
            tables = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).order_by(BilliardTable.id).all()
        
        result = []
        for t in tables:
            active_session = db.query(PlaySession).filter(
                PlaySession.table_id == t.id,
                PlaySession.status == "ACTIVE"
            ).first()
            
            session_data = None
            if active_session:
                items = db.query(SessionOrderItem).filter(
                    SessionOrderItem.session_id == active_session.id
                ).all()
                items_list = [
                    {"id": item.id, "item_name": item.item_name, "quantity": item.quantity,
                     "price": item.price, "total_price": item.total_price}
                    for item in items
                ]
                session_data = {
                    "id": active_session.id,
                    "start_time": active_session.start_time.isoformat() + "Z",
                    "order_items": items_list
                }
                
            result.append({
                "id": t.id,
                "store_id": t.store_id,
                "name": t.name,
                "camera_url": t.camera_url,
                "current_status": t.current_status,
                "table_type": t.table_type,
                "table_tier": t.table_tier,
                "price_per_hour": t.price_per_hour,
                "qr_token": generate_table_token(t.id),
                "active_session": session_data
            })
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/admin/tables/add")
def admin_add_table(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    name = payload.get("name", "").strip()
    table_type = payload.get("table_type", "LIP")
    table_tier = payload.get("table_tier", "STANDARD")
    price_per_hour = float(payload.get("price_per_hour", 50000.0))
    camera_url = payload.get("camera_url", "").strip()
    
    if not name:
        return JSONResponse({"status": "error", "message": "Vui long nhap ten ban"}, status_code=400)
        
    db = SessionLocal()
    try:
        new_table = BilliardTable(
            store_id=ctx.store_id,
            name=name,
            camera_url=camera_url,
            table_type=table_type,
            table_tier=table_tier,
            price_per_hour=price_per_hour,
            current_status="EMPTY"
        )
        db.add(new_table)
        db.commit()
        return JSONResponse({"status": "ok", "message": "Da them ban moi thanh cong"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.post("/admin/tables/update")
def admin_update_table(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    table_id = payload.get("id")
    name = payload.get("name", "").strip()
    table_type = payload.get("table_type", "LIP")
    table_tier = payload.get("table_tier", "STANDARD")
    price_per_hour = float(payload.get("price_per_hour", 50000.0))
    camera_url = payload.get("camera_url", "").strip()
    
    if not table_id or not name:
        return JSONResponse({"status": "error", "message": "Thieu thong tin ban"}, status_code=400)
        
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == table_id, BilliardTable.store_id == ctx.store_id).first() if ctx.role.value != 'SUPER_ADMIN' else db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Khong tim thay ban"}, status_code=404)
            
        table.name = name
        table.table_type = table_type
        table.table_tier = table_tier
        table.price_per_hour = price_per_hour
        table.camera_url = camera_url
        db.commit()
        return JSONResponse({"status": "ok", "message": "Da cap nhat thong tin ban"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.delete("/admin/tables/{table_id}")
def delete_table(table_id: int, ctx: StoreContext = Depends(require_write_permission)):
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == table_id, BilliardTable.store_id == ctx.store_id, BilliardTable.deleted_at == None).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Table not found"}, status_code=404)
            
        if table.current_status != TableStatus.EMPTY.value:
            return JSONResponse({"status": "error", "message": "Cannot delete table that is playing"}, status_code=400)
            
        table.deleted_at = datetime.utcnow()
        db.commit()
        return JSONResponse({"status": "success", "message": f"Deleted table {table.name}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.get("/{table_id}")
def get_table_info(table_id: int):
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Không tìm thấy bàn"}, status_code=404)
        return {"id": table.id, "name": table.name, "store_id": table.store_id, "current_status": table.current_status}
    finally:
        db.close()
