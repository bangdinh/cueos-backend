from typing import List, Dict, Optional, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Any] = []
        self.connections_by_store: Dict[int, List[Any]] = {}
        self.hq_connections: List[Any] = []
        self.ws_to_sid: Dict[Any, str] = {}
        self.latest_payload = "{}"
        self.loop = None

    async def connect(self, websocket: Any, store_id: Optional[int] = 1, is_hq: bool = False, sid: Optional[str] = None):
        import asyncio
        if self.loop is None:
            self.loop = asyncio.get_running_loop()
        await websocket.accept()
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
            
        if sid:
            self.ws_to_sid[websocket] = sid
            
        if is_hq or store_id is None or store_id == 0:
            if websocket not in self.hq_connections:
                self.hq_connections.append(websocket)
        else:
            if store_id not in self.connections_by_store:
                self.connections_by_store[store_id] = []
            if websocket not in self.connections_by_store[store_id]:
                self.connections_by_store[store_id].append(websocket)
                
        print(f"[WebSocket] Client connected (store_id={store_id}, is_hq={is_hq}, sid={sid}). Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: Any):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.hq_connections:
            self.hq_connections.remove(websocket)
        if websocket in self.ws_to_sid:
            del self.ws_to_sid[websocket]
        for store_id, conns in self.connections_by_store.items():
            if websocket in conns:
                conns.remove(websocket)
        print(f"[WebSocket] Client disconnected.")

    async def broadcast(self, message: str, store_id: Optional[int] = None):
        self.latest_payload = message
        target_connections = []
        
        # Luôn gửi cho các kết nối của Trụ sở HQ
        target_connections.extend(self.hq_connections)
        
        # Nếu chỉ định store_id, chỉ gửi cho các client của store đó
        if store_id is not None and store_id != 0:
            target_connections.extend(self.connections_by_store.get(store_id, []))
        else:
            # Nếu broadcast global (hoặc từ worker không rõ store), gửi cho tất cả
            target_connections.extend(self.active_connections)
            
        for connection in set(target_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[WebSocket] Send error: {e}")

    def broadcast_sync(self, message: str, store_id: Optional[int] = None):
        if self.loop and self.loop.is_running():
            import asyncio
            asyncio.run_coroutine_threadsafe(self.broadcast(message, store_id=store_id), self.loop)

websocket_manager = ConnectionManager()
