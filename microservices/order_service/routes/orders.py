import json
import time
import re
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import redis as redis_lib

from ..database import SessionLocal
from ..models.session import PlaySession, SessionOrderItem
from ..models.billiard_table import BilliardTable
from ..models.product import Product

# Token generator helper
import hashlib
SECRET_KEY = "BIDA_AI_SECURE_KEY_2026"
def generate_table_token(table_id: int) -> str:
    return hashlib.md5(f"{SECRET_KEY}_{table_id}".encode()).hexdigest()[:8]

def broadcast_to_websocket(event_data: dict, store_id: int):
    """
    Publish to redis so the monolith (which holds websocket connections) can broadcast it.
    """
    try:
        r = redis_lib.Redis(host='127.0.0.1', port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        event_data['store_id'] = store_id
        r.publish('bida_ai_events_order', json.dumps(event_data))
    except Exception as e:
        print(f"Failed to publish to redis: {e}")

# Fake StoreContext for now (since this microservice doesn't have the auth middleware yet)
class StoreContext:
    def __init__(self, store_id: int, role: str):
        self.store_id = store_id
        self.role = role
    def require_write_permission(self):
        pass

def get_store_context():
    return StoreContext(store_id=1, role="STORE_MANAGER")

router = APIRouter(prefix="/api", tags=["Orders"])

@router.post("/customer-order/{table_id}/{token}")
def customer_order(table_id: int, token: str, payload: dict):
    if token != generate_table_token(table_id):
        return JSONResponse({"status": "error", "message": "Mã xác thực không hợp lệ. Vui lòng quét lại QR!"}, status_code=403)
        
    items = payload.get("items", [])
    note = payload.get("note", "").strip()
    phone = payload.get("customer_phone", payload.get("phone", "")).strip()
    customer_name = payload.get("customer_name", "").strip()
    
    if not items:
        return JSONResponse({"status": "error", "message": "Giỏ hàng trống"}, status_code=400)
        
    if phone and not re.match(r"^(0|\+84|84)[35789]\d{8}$", phone):
        return JSONResponse({"status": "error", "message": "Số điện thoại Việt Nam không hợp lệ!"}, status_code=400)
        
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Bàn không tồn tại"}, status_code=404)
        if table.current_status != "PLAYING":
            return JSONResponse({"status": "error", "message": "Bàn chưa được bắt đầu tính giờ chơi. Vui lòng báo nhân viên bật bàn trước!"}, status_code=400)
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn chưa được bật chơi. Vui lòng báo nhân viên bật bàn trước!"}, status_code=400)
            
        normalized_items = []
        for item in items:
            item_name = item.get("item_name", item.get("name", "")).strip()
            quantity = int(item.get("quantity", item.get("qty", 1)))
            price = float(item.get("price", 0))
            item_note = item.get("note", "").strip()
            
            if not item_name or quantity <= 0:
                continue
                
            product = db.query(Product).filter(Product.name == item_name).first()
            if product:
                product.stock -= quantity
                if product.stock < 0: product.stock = 0

            existing_item = db.query(SessionOrderItem).filter(
                SessionOrderItem.session_id == active_session.id,
                SessionOrderItem.item_name == item_name
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.total_price = existing_item.quantity * existing_item.price
            else:
                new_item = SessionOrderItem(
                    session_id=active_session.id,
                    product_id=product.id if product else None,
                    item_name=item_name,
                    quantity=quantity,
                    price=price,
                    total_price=quantity * price
                )
                db.add(new_item)
                
            normalized_items.append({
                "item_name": item_name,
                "name": item_name,
                "quantity": quantity,
                "qty": quantity,
                "price": price,
                "total_price": quantity * price,
                "note": item_note
            })
            
        db.commit()

        name_label = f" ({customer_name})" if customer_name else ""
        has_paid_item = any(it.get("price", 0) > 0 for it in normalized_items)
        message_text = f"Khách {table.name}{name_label} vừa gọi đồ..." if has_paid_item else f"Khách {table.name}{name_label} đã yêu cầu:"

        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "store_id": table.store_id,
            "event_type": "CUSTOMER_ORDER",
            "message": message_text,
            "customer_phone": phone,
            "customer_name": customer_name,
            "note": note,
            "items": normalized_items
        }
        
        broadcast_to_websocket(event_data, table.store_id)

        return JSONResponse({"status": "ok", "message": "Gửi yêu cầu thành công!", "items": normalized_items})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/session/add-item/{table_id}")
def add_item_to_session(table_id: int, payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    item_name = payload.get("item_name", "").strip()
    quantity = int(payload.get("quantity", 1))
    price = float(payload.get("price", 0))
    
    if not item_name or quantity <= 0 or price < 0:
        return JSONResponse({"status": "error", "message": "Dữ liệu món ăn không hợp lệ"}, status_code=400)
        
    db = SessionLocal()
    try:
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn chưa được bật tính giờ"}, status_code=400)
            
        existing_item = db.query(SessionOrderItem).filter(
            SessionOrderItem.session_id == active_session.id,
            SessionOrderItem.item_name == item_name
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.total_price = existing_item.quantity * existing_item.price
        else:
            new_item = SessionOrderItem(
                session_id=active_session.id,
                item_name=item_name,
                quantity=quantity,
                price=price,
                total_price=quantity * price
            )
            db.add(new_item)
            
        db.commit()
        return JSONResponse({"status": "ok", "message": f"Đã thêm món vào bàn"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/session/add-items/{table_id}")
def add_items_to_session(table_id: int, payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    items = payload.get("items", [])
    
    if not items or len(items) == 0:
        return JSONResponse({"status": "error", "message": "Giỏ hàng trống!"}, status_code=400)
        
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Không tìm thấy bàn!"}, status_code=404)
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn chưa được bắt đầu tính giờ chơi!"}, status_code=400)
            
        added_count = 0
        for item in items:
            item_name = item.get("item_name", item.get("name", "")).strip()
            quantity = int(item.get("quantity", item.get("qty", 1)))
            price = float(item.get("price", 0))
            
            if not item_name or quantity <= 0 or price < 0:
                continue
                
            product = db.query(Product).filter(Product.name == item_name).first()
            if product:
                product.stock -= quantity
                if product.stock < 0: product.stock = 0

            existing_item = db.query(SessionOrderItem).filter(
                SessionOrderItem.session_id == active_session.id,
                SessionOrderItem.item_name == item_name
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.total_price = existing_item.quantity * existing_item.price
            else:
                new_item = SessionOrderItem(
                    session_id=active_session.id,
                    product_id=product.id if product else None,
                    item_name=item_name,
                    quantity=quantity,
                    price=price,
                    total_price=quantity * price
                )
                db.add(new_item)
            added_count += 1
                
        db.commit()

        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "CUSTOMER_ORDER",
            "message": f"Thu ngân đã thêm {added_count} món vào hóa đơn {table.name}!",
            "items": items
        }
        broadcast_to_websocket(event_data, table.store_id)

        return JSONResponse({"status": "ok", "message": f"Đã thêm {added_count} món vào hóa đơn {table.name}!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.delete("/session/item/{item_id}")
def delete_session_item(item_id: int, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    db = SessionLocal()
    try:
        item = db.query(SessionOrderItem).filter(SessionOrderItem.id == item_id).first()
        if not item:
            return JSONResponse({"status": "error", "message": "Không tìm thấy món ăn trong bill"}, status_code=404)
        
        session = db.query(PlaySession).filter(PlaySession.id == item.session_id).first()
        if not session or session.status != "ACTIVE":
            return JSONResponse({"status": "error", "message": "Chỉ có thể sửa đổi bill của bàn đang chơi"}, status_code=400)
            
        item_name = item.item_name
        table_id = session.table_id
        db.delete(item)
        db.commit()
        
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "BILL_ITEM_UPDATED",
            "message": f"Thu ngân đã xóa món '{item_name}' khỏi hóa đơn."
        }
        broadcast_to_websocket(event_data, session.store_id)
            
        return JSONResponse({"status": "ok", "message": "Đã xóa món khỏi hóa đơn!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/session/item/{item_id}/update")
def update_session_item(item_id: int, payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    new_qty = int(payload.get("quantity", 0))
    db = SessionLocal()
    try:
        item = db.query(SessionOrderItem).filter(SessionOrderItem.id == item_id).first()
        if not item:
            return JSONResponse({"status": "error", "message": "Không tìm thấy món trong bill"}, status_code=404)
            
        session = db.query(PlaySession).filter(PlaySession.id == item.session_id).first()
        if not session or session.status != "ACTIVE":
            return JSONResponse({"status": "error", "message": "Chỉ có thể sửa đổi bill của bàn đang chơi"}, status_code=400)
            
        table_id = session.table_id
        item_name = item.item_name
        if new_qty <= 0:
            db.delete(item)
            msg = f"Đã xóa món '{item_name}' khỏi hóa đơn!"
        else:
            item.quantity = new_qty
            item.total_price = item.quantity * item.price
            msg = f"Đã cập nhật số lượng '{item_name}' thành {new_qty}!"
            
        db.commit()
        
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "BILL_ITEM_UPDATED",
            "message": msg
        }
        broadcast_to_websocket(event_data, session.store_id)
            
        return JSONResponse({"status": "ok", "message": msg})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()
