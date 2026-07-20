import json
import redis
import asyncio
import threading
from datetime import datetime
import math
from database.database import SessionLocal
from database.crud import save_ai_event
from database.models import PlaySession, BilliardTable
from api.websocket_server import websocket_manager

def start_redis_listener_thread(loop):
    def listener():
        try:
            # Sử dụng Redis đồng bộ
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            pubsub = redis_client.pubsub()
            pubsub.subscribe('bida_ai_events')
            print("[API] ✅ Đã khởi động luồng lắng nghe Redis (Thread riêng)")

            for message in pubsub.listen():
                if message['type'] != 'message':
                    continue
                try:
                    data = json.loads(message['data'])
                except Exception as e:
                    print(f"[API ERROR] Lỗi parse JSON từ Redis: {e}")
                    continue

                table_id = data.get("table_id")
                event_type = data.get("event_type")
                confidence = data.get("confidence", 1.0)
                image_base64 = data.get("image", None)
                
                db = SessionLocal()
                play_time_str = "Chưa bắt đầu"
                total_fee_str = "0 đ"
                date_str = datetime.now().strftime("%d/%m/%Y")
                
                try:
                    save_ai_event(db, table_id, event_type, confidence)
                    
                    # Lấy thông tin phiên chơi để tính tiền và thời gian
                    table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
                    session = db.query(PlaySession).filter(PlaySession.table_id == table_id).order_by(PlaySession.id.desc()).first()
                    
                    if session:
                        date_str = session.start_time.strftime("%d/%m/%Y")
                        
                        # Tính thời gian đã chơi
                        end_t = session.end_time if session.end_time else datetime.utcnow()
                        diff = end_t - session.start_time
                        diff_seconds = diff.total_seconds()
                        
                        hours = int(diff_seconds // 3600)
                        minutes = int((diff_seconds % 3600) // 60)
                        
                        if hours > 0:
                            play_time_str = f"{hours} giờ {minutes} phút"
                        else:
                            play_time_str = f"{minutes} phút"
                            
                        # Tính tiền
                        total_minutes = math.ceil(diff_seconds / 60)
                        price = table.price_per_hour if table else 50000.0
                        fee = (total_minutes / 60) * price
                        total_fee_str = f"{int(fee):,} đ"
                except Exception as e:
                    print(f"[DB Error] Lỗi ghi DB hoặc tính hóa đơn: {e}")
                finally:
                    db.close()
                
                # Đóng gói dữ liệu thành JSON để gửi xuống Trình duyệt Web
                import time
                ws_payload = {
                    "id": f"evt_{time.time()}",
                    "table_id": table_id,
                    "event_type": event_type,
                    "message": "",
                    "image": image_base64,
                    "date": date_str,
                    "play_time": play_time_str,
                    "total_fee": total_fee_str
                }
                
                if event_type == "HAND_RAISED":
                    ws_payload["message"] = f"🛎️ KHẨN: Bàn {table_id} có khách vẫy tay gọi!"
                elif event_type == "TABLE_ACTIVE":
                    ws_payload["message"] = f"🎱 Bàn {table_id} vừa bắt đầu chơi."
                elif event_type == "TABLE_EMPTY":
                    ws_payload["message"] = f"✅ Bàn {table_id} đã dừng chơi."

                # Ghi trực tiếp vào Redis Key (latest_ai_event) để Web API đọc được ngay lập tức
                payload_str = json.dumps(ws_payload)
                print(f"[API DEBUG] Đã đẩy {len(payload_str)} bytes lên Web API (AJAX Polling)...")
                redis_client.set('latest_ai_event', payload_str)
                websocket_manager.latest_payload = payload_str

        except Exception as e:
            print(f"[API] Mất kết nối Redis trong Thread: {e}")

    # Khởi động Thread chạy ngầm (Daemon)
    t = threading.Thread(target=listener, daemon=True)
    t.start()
