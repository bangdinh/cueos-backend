import os
import json
import time
import re
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
import redis as redis_lib

from ..database import SessionLocal
from database.models.order_item import SessionOrderItem

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
        r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        event_data['store_id'] = store_id
        r.publish('bida_ai_events_order', json.dumps(event_data))
    except Exception as e:
        print(f"Failed to publish to redis: {e}")

def publish_deduct_stock(store_id: int, items_to_deduct: list):
    try:
        r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        event_data = {
            "event_type": "DEDUCT_STOCK",
            "store_id": store_id,
            "items": items_to_deduct
        }
        r.xadd('stream:inventory_events', {'payload': json.dumps(event_data)})
    except Exception as e:
        print(f"Failed to xadd deduct stock event: {e}")


async def get_active_session_from_service(table_id: int):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{os.environ.get('SESSION_SERVICE_URL', 'http://127.0.0.1:8006')}/api/session/active/{table_id}")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"Failed to connect to Session Service: {e}")
    return None

async def get_inventory_products(store_id: int, request: Request = None):
    headers = {}
    if request and "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{os.environ.get('INVENTORY_SERVICE_URL', 'http://127.0.0.1:8002')}/api/products?store_id={store_id}", headers=headers)
            if resp.status_code == 200:
                return {p["name"]: p for p in resp.json()}
    except Exception as e:
        print(f"Error fetching inventory: {e}")
    return {}

# Fake StoreContext for now (since this microservice doesn't have the auth middleware yet)
class StoreContext:
    def __init__(self, store_id: int, role: str):
        self.store_id = store_id
        self.role = role
    def require_write_permission(self):
        pass

def get_store_context():
    return StoreContext(store_id=1, role="MANAGER")

router = APIRouter(prefix="/api", tags=["Orders"])

@router.post("/customer-order/{table_id}/{token}")
async def customer_order(table_id: int, token: str, payload: dict):
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
        active_session = await get_active_session_from_service(table_id)
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn không tồn tại hoặc chưa bật chơi!"}, status_code=400)
            
        session_id = active_session["id"]
        store_id = active_session["store_id"]
        
        inventory = await get_inventory_products(store_id)
        
        normalized_items = []
        items_to_deduct = []
        for item in items:
            item_name = item.get("item_name", item.get("name", "")).strip()
            quantity = int(item.get("quantity", item.get("qty", 1)))
            item_note = item.get("note", "").strip()
            
            if not item_name or quantity <= 0:
                continue
                
            inv_item = inventory.get(item_name)
            if inv_item:
                price = float(inv_item["price"])
                items_to_deduct.append({"name": item_name, "quantity": quantity})
            else:
                price = float(item.get("price", 0))

            existing_item = db.query(SessionOrderItem).filter(
                SessionOrderItem.session_id == session_id,
                SessionOrderItem.item_name == item_name
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.total_price = existing_item.quantity * existing_item.price
            else:
                new_item = SessionOrderItem(
                    session_id=session_id,
                    product_id=inv_item["id"] if inv_item else None,
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
        
        if items_to_deduct:
            publish_deduct_stock(store_id, items_to_deduct)

        name_label = f" ({customer_name})" if customer_name else ""
        has_paid_item = any(it.get("price", 0) > 0 for it in normalized_items)
        message_text = f"Khách Bàn {table_id}{name_label} vừa gọi đồ..." if has_paid_item else f"Khách Bàn {table_id}{name_label} đã yêu cầu:"

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
        
        broadcast_to_websocket(event_data, store_id)

        return JSONResponse({"status": "ok", "message": "Gửi yêu cầu thành công!", "items": normalized_items})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/session/add-item/{table_id}")
async def add_item_to_session(table_id: int, payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    item_name = payload.get("item_name", "").strip()
    quantity = int(payload.get("quantity", 1))
    price = float(payload.get("price", 0))
    
    if not item_name or quantity <= 0 or price < 0:
        return JSONResponse({"status": "error", "message": "Dữ liệu món ăn không hợp lệ"}, status_code=400)
        
    db = SessionLocal()
    try:
        active_session = await get_active_session_from_service(table_id)
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn chưa được bật tính giờ"}, status_code=400)
            
        session_id = active_session["id"]
        store_id = active_session["store_id"]
        
        inventory = await get_inventory_products(store_id)
        inv_item = inventory.get(item_name)
        if inv_item:
            price = float(inv_item["price"])
            publish_deduct_stock(ctx.store_id, [{"name": item_name, "quantity": quantity}])
            
        existing_item = db.query(SessionOrderItem).filter(
            SessionOrderItem.session_id == session_id,
            SessionOrderItem.item_name == item_name
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.total_price = existing_item.quantity * existing_item.price
        else:
            new_item = SessionOrderItem(
                session_id=session_id,
                product_id=inv_item["id"] if inv_item else None,
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
async def add_items_to_session(table_id: int, payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_write_permission()
    items = payload.get("items", [])
    
    if not items or len(items) == 0:
        return JSONResponse({"status": "error", "message": "Giỏ hàng trống!"}, status_code=400)
        
    db = SessionLocal()
    try:
        active_session = await get_active_session_from_service(table_id)
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn không tồn tại hoặc chưa bật chơi!"}, status_code=400)
            
        session_id = active_session["id"]
        store_id = active_session["store_id"]
        
        inventory = await get_inventory_products(store_id)
        
        added_count = 0
        items_to_deduct = []
        for item in items:
            item_name = item.get("item_name", item.get("name", "")).strip()
            quantity = int(item.get("quantity", item.get("qty", 1)))
            
            if not item_name or quantity <= 0:
                continue
                
            inv_item = inventory.get(item_name)
            if inv_item:
                price = float(inv_item["price"])
                items_to_deduct.append({"name": item_name, "quantity": quantity})
            else:
                price = float(item.get("price", 0))

            existing_item = db.query(SessionOrderItem).filter(
                SessionOrderItem.session_id == session_id,
                SessionOrderItem.item_name == item_name
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.total_price = existing_item.quantity * existing_item.price
            else:
                new_item = SessionOrderItem(
                    session_id=session_id,
                    product_id=inv_item["id"] if inv_item else None,
                    item_name=item_name,
                    quantity=quantity,
                    price=price,
                    total_price=quantity * price
                )
                db.add(new_item)
            added_count += 1
                
        db.commit()
        
        if items_to_deduct:
            publish_deduct_stock(store_id, items_to_deduct)

        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "CUSTOMER_ORDER",
            "message": f"Thu ngân đã thêm {added_count} món vào hóa đơn!",
            "items": items
        }
        broadcast_to_websocket(event_data, store_id)

        return JSONResponse({"status": "ok", "message": f"Đã thêm {added_count} món vào hóa đơn!"})
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
        
        # In a true microservice we would verify with Session Service,
        # but for simplicity we assume the UI only allows deleting active items.
        table_id = "Không xác định"
        store_id = item.store_id
        db.delete(item)
        db.commit()
        
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "BILL_ITEM_UPDATED",
            "message": f"Thu ngân đã xóa món '{item_name}' khỏi hóa đơn."
        }
        broadcast_to_websocket(event_data, store_id)
            
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
            
        # In a true microservice we would verify with Session Service,
        # but for simplicity we assume the UI only allows deleting active items.
        table_id = "Không xác định"
        store_id = item.store_id
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
        broadcast_to_websocket(event_data, store_id)
            
        return JSONResponse({"status": "ok", "message": msg})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.get("/session/orders/{session_id}")
def get_session_orders_for_billing(session_id: int):
    db = SessionLocal()
    try:
        items = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == session_id).all()
        return JSONResponse({"status": "success", "items": [{"name": i.item_name, "quantity": i.quantity, "price": i.price, "total_price": i.total_price} for i in items]})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()
