import os
import json
import redis
import threading
import time
from .database import SessionLocal
from .models.product import Product

def start_redis_listener_thread():
    def listener():
        redis_host = os.environ.get('REDIS_HOST', '127.0.0.1')
        stream_name = 'stream:inventory_events'
        group_name = 'inventory_group'
        consumer_name = 'inventory_worker_1'

        while True:
            try:
                redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
                
                # Create consumer group if it doesn't exist
                try:
                    redis_client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
                    print(f"[Inventory Service] Created consumer group {group_name}")
                except redis.exceptions.ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        print(f"[Inventory Service] Group create error: {e}")

                print(f"[Inventory Service] Listening on Redis Stream {stream_name} (DEDUCT_STOCK)")

                while True:
                    try:
                        # Block for 2 seconds waiting for messages
                        messages = redis_client.xreadgroup(group_name, consumer_name, {stream_name: '>'}, count=10, block=2000)
                        
                        if not messages:
                            continue

                        for stream, message_list in messages:
                            for message_id, message_data in message_list:
                                try:
                                    payload_str = message_data.get('payload')
                                    if not payload_str:
                                        redis_client.xack(stream_name, group_name, message_id)
                                        continue
                                        
                                    data = json.loads(payload_str)
                                    event_type = data.get("event_type")
                                    
                                    if event_type == "DEDUCT_STOCK":
                                        items = data.get("items", [])
                                        store_id = data.get("store_id")
                                        
                                        if items:
                                            db = SessionLocal()
                                            try:
                                                for item in items:
                                                    item_name = item.get("name")
                                                    qty = item.get("quantity", 0)
                                                    
                                                    product = db.query(Product).filter(
                                                        Product.name == item_name, 
                                                        Product.store_id == store_id
                                                    ).first()
                                                    
                                                    if product:
                                                        product.stock -= qty
                                                        if product.stock < 0: 
                                                            product.stock = 0
                                                        print(f"[Inventory Service] Đã tự động trừ {qty} cái cho '{item_name}' (Còn {product.stock})")
                                                db.commit()
                                            except Exception as e:
                                                print(f"[Inventory Error] Lỗi khi trừ kho: {e}")
                                            finally:
                                                db.close()
                                                
                                    # Acknowledge the message so it's not processed again
                                    redis_client.xack(stream_name, group_name, message_id)
                                    
                                except Exception as e:
                                    print(f"[Inventory Error] Lỗi xử lý message {message_id}: {e}")
                                    
                    except redis.ConnectionError:
                        print("[Inventory Service] Mất kết nối Redis. Đang thử lại...")
                        break
                    
            except Exception as e:
                print(f"[Inventory Service] Lỗi Redis: {e}")
                time.sleep(5)

    t = threading.Thread(target=listener, daemon=True)
    t.start()
