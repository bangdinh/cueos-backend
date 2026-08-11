from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
import json

from api.redis_listener import start_redis_listener_thread
from api.websocket_server import websocket_manager
from database.database import init_db, SessionLocal
from database.crud import seed_initial_tables, seed_initial_products
from database.seed import seed_default_store_and_users
from database.models import BilliardTable, PlaySession, SessionOrderItem, Product, CustomerModel, UserRole

# Import HTML Templates
from templates.admin_template import admin_html
from templates.customer_template import customer_menu_html

# Import Modular API Routers
from api.routes import products, tables, client_realtime, reports
from api import auth
from api.routes.client_realtime import generate_table_token

CLIPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips")
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs("assets", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    seed_default_store_and_users(db)
    for s_id in [1, 2, 3]:
        seed_initial_tables(db, store_id=s_id)
        seed_initial_products(db, store_id=s_id)
    db.close()
    loop = asyncio.get_running_loop()
    start_redis_listener_thread(loop)
    from workers.sync_hq_worker import start_sync_worker_daemon
    start_sync_worker_daemon(interval_seconds=60)
    yield

app = FastAPI(title="Bida AI Management System", lifespan=lifespan)

# Mount static files directories
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Include Modular Routers
app.include_router(products.router)
app.include_router(tables.router)
app.include_router(client_realtime.router)
app.include_router(reports.router)
app.include_router(auth.router)

# Page Routes
@app.get("/")
async def get_admin_dashboard():
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return HTMLResponse(content=admin_html, headers=headers)

@app.get("/menu/{table_id}/{token}")
async def customer_menu(table_id: int, token: str):
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return HTMLResponse(content="<h1>Bàn không tồn tại</h1>", status_code=404)
        
        if token != generate_table_token(table_id):
            return HTMLResponse(content="<h1 style='text-align:center; padding: 20px; font-family: sans-serif; color: #ef4444;'>Lỗi: Đường dẫn không hợp lệ. Vui lòng quét lại mã QR tại bàn!</h1>", status_code=403)
            
        products_db = db.query(Product).all()
        stock_json = json.dumps({p.name: p.stock for p in products_db})
        
        cats = ["Tất cả", "Nước uống", "Đồ ăn", "Thuốc lá", "Dịch vụ khác", "🛎️ Yêu cầu nghiệp vụ"]
        cat_order = {c: i for i, c in enumerate(cats)}
        
        def get_cat_rank(category):
            cat_norm = (category or "").strip()
            return cat_order.get(cat_norm, 99)
            
        sorted_prods = sorted(products_db, key=lambda p: (get_cat_rank(p.category), p.id))
        
        dynamic_menu_list = []
        for p in sorted_prods:
            dynamic_menu_list.append({
                "id": p.id,
                "name": p.name,
                "category": p.category or "Thức uống",
                "price": p.price,
                "stock": p.stock,
                "image_url": p.image_url or ""
            })
        dynamic_menu_json = json.dumps(dynamic_menu_list)
        
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        active_start_time = "None"
        ordered_items = []
        if active_session:
            active_start_time = active_session.start_time.isoformat() + "Z"
            items_db = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == active_session.id).all()
            for item in items_db:
                ordered_items.append({
                    "name": item.item_name,
                    "qty": item.quantity,
                    "total": item.total_price
                })
            
        rendered_html = customer_menu_html.replace("{table_id}", str(table_id))\
                                          .replace("{table_name}", table.name)\
                                          .replace("{qr_token}", token)\
                                          .replace("{inventory_stock_json}", stock_json)\
                                          .replace("{dynamic_menu_json}", dynamic_menu_json)\
                                          .replace("{active_start_time}", active_start_time)\
                                          .replace("{order_history_json}", json.dumps(ordered_items))
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        return HTMLResponse(content=rendered_html, headers=headers)
    finally:
        db.close()

# WebSocket Realtime Endpoint
@app.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    from api.auth import verify_token
    auth_header = websocket.headers.get("authorization")
    jwt_str = None
    if token:
        jwt_str = token
    elif auth_header and auth_header.startswith("Bearer "):
        jwt_str = auth_header.split(" ")[1]
        
    if not jwt_str:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    try:
        payload = verify_token(jwt_str)
        role_str = str(payload.get("role", "STORE_MANAGER")).upper()
        is_hq = (role_str == UserRole.SUPER_ADMIN.value)
        token_store_id = payload.get("store_id")
        sid = payload.get("sid")
        if not is_hq and token_store_id is None:
            token_store_id = 1
        elif token_store_id is not None:
            token_store_id = int(token_store_id)
            
        await websocket_manager.connect(websocket, store_id=token_store_id, is_hq=is_hq, sid=sid)
        try:
            while True:
                data = await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
