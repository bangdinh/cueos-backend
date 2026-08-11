import os
import json
import csv
import io
import time
import re
import math
from datetime import datetime
from fastapi import APIRouter, Response, Depends
from api.middleware.store_context import StoreContext, get_store_context
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from ..database import SessionLocal
from ..models.product import Product
from pydantic import BaseModel

class DecreaseStockRequest(BaseModel):
    name: str
    quantity: int
from api.websocket_server import websocket_manager

# Token generator helper
import hashlib
SECRET_KEY = "BIDA_AI_SECURE_KEY_2026"
def generate_table_token(table_id: int) -> str:
    return hashlib.md5(f"{SECRET_KEY}_{table_id}".encode()).hexdigest()[:8]

CLIPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "clips")
client_messages_store = {}

router = APIRouter(prefix="/api", tags=["Products"])

@router.get("/inventory")
def get_inventory(store_id: int = None, ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        target = store_id if (ctx.role.value == 'SUPER_ADMIN' and store_id) else ctx.store_id
        products = db.query(Product).filter(Product.store_id == target).all() if target else db.query(Product).all()
        stock_dict = {p.name: p.stock for p in products}
        return JSONResponse(stock_dict)
    finally:
        db.close()

@router.get("/products")
def list_products(store_id: int = None, ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        target = store_id if (ctx.role.value == 'SUPER_ADMIN' and store_id) else ctx.store_id
        products = db.query(Product).filter(Product.store_id == target).order_by(Product.id).all() if target else db.query(Product).order_by(Product.id).all()
        return JSONResponse([
            {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "category": p.category, "image_url": p.image_url or ""}
            for p in products
        ])
    finally:
        db.close()

@router.post("/products/add")
def add_product(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    name = payload.get("name", "").strip()
    price = float(payload.get("price", 0))
    stock = int(payload.get("stock", 0))
    category = payload.get("category", "").strip() or "Thức uống"
    image_url = payload.get("image_url", "").strip()
    
    if not name:
        return JSONResponse({"status": "error", "message": "Vui lòng nhập tên sản phẩm!"}, status_code=400)
    if price < 1000:
        return JSONResponse({"status": "error", "message": "Đơn giá phải từ 1.000 VNĐ trở lên!"}, status_code=400)
    if stock < 0:
        return JSONResponse({"status": "error", "message": "Số lượng tồn kho không được âm!"}, status_code=400)
        
    db = SessionLocal()
    try:
        exists = db.query(Product).filter(Product.name == name).first()
        if exists:
            return JSONResponse({"status": "error", "message": f"Sản phẩm '{name}' đã có sẵn trong thực đơn!"}, status_code=400)
            
        new_prod = Product(name=name, price=price, stock=stock, category=category, image_url=image_url, store_id=ctx.store_id)
        db.add(new_prod)
        db.commit()
        return JSONResponse({"status": "ok", "message": f"Đã thêm sản phẩm '{name}' vào thực đơn thành công!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.post("/products/update")
def update_product(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    prod_id = int(payload.get("id"))
    price = float(payload.get("price", 0))
    stock = int(payload.get("stock", 0))
    image_url = payload.get("image_url", "").strip()
    category = payload.get("category", "").strip()
    
    if price < 1000 or stock < 0:
        return JSONResponse({"status": "error", "message": "Đơn giá phải từ 1000 VNĐ trở lên và tồn kho không được âm!"}, status_code=400)
        
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == prod_id, Product.store_id == ctx.store_id).first() if ctx.role.value != 'SUPER_ADMIN' else db.query(Product).filter(Product.id == prod_id).first()
        if not product:
            return JSONResponse({"status": "error", "message": "Sản phẩm không tồn tại"}, status_code=404)
            
        product.price = price
        product.stock = stock
        product.image_url = image_url
        if category:
            product.category = category
        db.commit()
        return JSONResponse({"status": "ok", "message": "Đã cập nhật sản phẩm!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.delete("/products/delete/{prod_id}")
def delete_product(prod_id: int, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == prod_id, Product.store_id == ctx.store_id).first() if ctx.role.value != 'SUPER_ADMIN' else db.query(Product).filter(Product.id == prod_id).first()
        if not product:
            return JSONResponse({"status": "error", "message": "Sản phẩm không tồn tại"}, status_code=404)
            
        db.delete(product)
        db.commit()
        return JSONResponse({"status": "ok", "message": "Đã xóa sản phẩm!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.post("/products/batch-update")
def batch_update_products(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    items = payload.get("items", [])
    if not items:
        return JSONResponse({"status": "error", "message": "Không có sản phẩm nào để cập nhật!"}, status_code=400)
        
    db = SessionLocal()
    try:
        updated_count = 0
        for item in items:
            prod_id = int(item.get("id"))
            price = float(item.get("price", 0))
            stock = int(item.get("stock", 0))
            category = item.get("category", "").strip()
            image_url = item.get("image_url", "").strip()
            
            if price < 1000 or stock < 0:
                continue
                
            product = db.query(Product).filter(Product.id == prod_id, Product.store_id == ctx.store_id).first() if ctx.role.value != 'SUPER_ADMIN' else db.query(Product).filter(Product.id == prod_id).first()
            if product:
                product.price = price
                product.stock = stock
                product.image_url = image_url
                if category:
                    product.category = category
                updated_count += 1
                
        db.commit()
        return JSONResponse({"status": "ok", "message": f"Đã lưu thành công tất cả {updated_count} sản phẩm!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@router.post("/products/batch-delete")
def batch_delete_products(payload: dict, ctx: StoreContext = Depends(get_store_context)):
    ctx.require_admin_permission()
    ids = payload.get("ids", [])
    if not ids:
        return JSONResponse({"status": "error", "message": "Vui lòng chọn sản phẩm cần xóa!"}, status_code=400)
        
    db = SessionLocal()
    try:
        deleted_count = 0
        for prod_id in ids:
            product = db.query(Product).filter(Product.id == int(prod_id)).first()
            if product:
                db.delete(product)
                deleted_count += 1
                
        db.commit()
        return JSONResponse({"status": "ok", "message": f"Đã xóa thành công {deleted_count} sản phẩm đã chọn!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()
