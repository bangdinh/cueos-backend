import json
import time
import redis
from typing import Dict, Any
from api.websocket_server import websocket_manager

# Lưu trữ tạm thời các message gửi cho client
client_messages_store: Dict[int, Any] = {}

class NotificationService:
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    @staticmethod
    def notify_admin_dashboard(store_id: int, event_type: str, message: str, payload: Dict[str, Any] = None):
        """
        Gửi thông báo Real-time (qua WebSocket) cho giao diện Thu ngân/Quản lý.
        """
        event_data = {
            "id": f"evt_{time.time()}",
            "store_id": store_id,
            "event_type": event_type,
            "message": message,
        }
        if payload:
            event_data.update(payload)
            
        try:
            websocket_manager.broadcast_sync(json.dumps(event_data), store_id=store_id)
        except Exception:
            pass

    @staticmethod
    def notify_client_qr(table_id: int, message: str, message_type: str = "info", redirect_url: str = ""):
        """
        Gửi thông báo ngược lại cho khách hàng quét mã QR (thông qua Redis polling).
        """
        data = {
            "message": message,
            "type": message_type,
            "redirect_url": redirect_url,
            "timestamp": time.time()
        }
        client_messages_store[table_id] = data
        try:
            r = redis.Redis(host=NotificationService.REDIS_HOST, port=NotificationService.REDIS_PORT, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
            r.set(f"client_msg_{table_id}", json.dumps(data))
            r.expire(f"client_msg_{table_id}", 300)
        except Exception:
            pass
            
    @staticmethod
    def poll_client_messages(table_id: int) -> Dict[str, Any]:
        """
        Khách hàng poll message.
        """
        data = None
        if table_id in client_messages_store:
            data = client_messages_store.pop(table_id)
        try:
            r = redis.Redis(host=NotificationService.REDIS_HOST, port=NotificationService.REDIS_PORT, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
            if data:
                r.delete(f"client_msg_{table_id}")
            else:
                msg = r.get(f"client_msg_{table_id}")
                if msg:
                    r.delete(f"client_msg_{table_id}")
                    data = json.loads(msg)
        except Exception:
            pass
            
        return data
