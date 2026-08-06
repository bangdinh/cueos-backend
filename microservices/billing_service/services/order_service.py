import time
from sqlalchemy.orm import Session
from ..models.session import SessionOrderItem, PlaySession
from .notification_service import NotificationService
from typing import List, Dict, Any
import httpx

INVENTORY_SERVICE_URL = "http://127.0.0.1:8002"

class OrderService:
    @staticmethod
    def _get_table_info(table_id: int):
        try:
            resp = httpx.get(f"{INVENTORY_SERVICE_URL}/api/tables/{table_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print("Error connecting to Inventory Service:", e)
            return None
            
    @staticmethod
    def _decrease_stock(item_name: str, quantity: int):
        try:
            resp = httpx.post(f"{INVENTORY_SERVICE_URL}/api/products/decrease-stock", json={"name": item_name, "quantity": quantity}, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def process_customer_order(db: Session, table_id: int, items: List[Dict], customer_name: str, phone: str, note: str):
        table = OrderService._get_table_info(table_id)
        if not table:
            raise ValueError("Bàn không tồn tại hoặc Inventory Service không phản hồi")
        if table.get("current_status") != "PLAYING":
            raise ValueError("Bàn chưa được bắt đầu tính giờ chơi. Vui lòng báo nhân viên bật bàn trước!")
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        if not active_session:
            raise ValueError("Bàn chưa được bật chơi. Vui lòng báo nhân viên bật bàn trước!")
            
        normalized_items = []
        for item in items:
            item_name = item.get("item_name", item.get("name", "")).strip()
            quantity = int(item.get("quantity", item.get("qty", 1)))
            price = float(item.get("price", 0))
            item_note = item.get("note", "").strip()
            
            if not item_name or quantity <= 0:
                continue
                
            OrderService._decrease_stock(item_name, quantity)

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
                    store_id=active_session.store_id,
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
        message_text = f"Khách {table['name']}{name_label} vừa gọi đồ..." if has_paid_item else f"Khách {table['name']}{name_label} đã yêu cầu:"

        payload = {
            "customer_phone": phone,
            "customer_name": customer_name,
            "note": note,
            "items": normalized_items,
            "table_id": table_id
        }
        
        NotificationService.notify_admin_dashboard(
            store_id=table["store_id"],
            event_type="CUSTOMER_ORDER",
            message=message_text,
            payload=payload
        )
        
        return normalized_items

    @staticmethod
    def add_items_by_staff(db: Session, table_id: int, items: List[Dict]):
        table = OrderService._get_table_info(table_id)
        if not table:
            raise ValueError("Không tìm thấy bàn hoặc Inventory Service không phản hồi!")
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            raise ValueError("Bàn chưa được bắt đầu tính giờ chơi!")
            
        added_count = 0
        for item in items:
            item_name = item.get("item_name", item.get("name", "")).strip()
            quantity = int(item.get("quantity", item.get("qty", 1)))
            price = float(item.get("price", 0))
            
            if not item_name or quantity <= 0 or price < 0:
                continue
                
            OrderService._decrease_stock(item_name, quantity)

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
                    store_id=active_session.store_id,
                    item_name=item_name,
                    quantity=quantity,
                    price=price,
                    total_price=quantity * price
                )
                db.add(new_item)
            added_count += 1
                
        db.commit()

        if added_count > 0:
            payload = {
                "items": items,
                "table_id": table_id
            }
            NotificationService.notify_admin_dashboard(
                store_id=table["store_id"],
                event_type="CUSTOMER_ORDER",
                message=f"Thu ngân đã thêm {added_count} món vào hóa đơn {table['name']}!",
                payload=payload
            )

        return added_count

    @staticmethod
    def update_order_item(db: Session, item_id: int, new_quantity: int):
        item = db.query(SessionOrderItem).filter(SessionOrderItem.id == item_id).first()
        if not item:
            raise ValueError("Không tìm thấy món trong bill")
            
        session = db.query(PlaySession).filter(PlaySession.id == item.session_id).first()
        if not session or session.status != "ACTIVE":
            raise ValueError("Chỉ có thể sửa đổi bill của bàn đang chơi")
            
        table_id = session.table_id
        item_name = item.item_name
        
        diff = new_quantity - item.quantity
        if diff > 0:
             OrderService._decrease_stock(item_name, diff)
        elif diff < 0:
             pass 

        if new_quantity <= 0:
            db.delete(item)
            msg = f"Đã xóa món '{item_name}' khỏi hóa đơn!"
        else:
            item.quantity = new_quantity
            item.total_price = item.quantity * item.price
            msg = f"Đã cập nhật số lượng '{item_name}' thành {new_quantity}!"
            
        db.commit()
        
        NotificationService.notify_admin_dashboard(
            store_id=session.store_id,
            event_type="BILL_ITEM_UPDATED",
            message=msg,
            payload={"table_id": table_id}
        )
        return msg

    @staticmethod
    def remove_order_item(db: Session, item_id: int):
        item = db.query(SessionOrderItem).filter(SessionOrderItem.id == item_id).first()
        if not item:
            raise ValueError("Không tìm thấy món ăn trong bill")
        
        session = db.query(PlaySession).filter(PlaySession.id == item.session_id).first()
        if not session or session.status != "ACTIVE":
            raise ValueError("Chỉ có thể sửa đổi bill của bàn đang chơi")
            
        item_name = item.item_name
        table_id = session.table_id
        db.delete(item)
        db.commit()
        
        NotificationService.notify_admin_dashboard(
            store_id=session.store_id,
            event_type="BILL_ITEM_UPDATED",
            message=f"Thu ngân đã xóa món '{item_name}' khỏi hóa đơn.",
            payload={"table_id": table_id}
        )
        return f"Đã xóa món '{item_name}' khỏi hóa đơn."
