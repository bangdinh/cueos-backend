import os

filepath = r"microservices\order_service\routes\orders.py"

endpoint_code = """
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
"""

with open(filepath, 'a', encoding='utf-8') as f:
    f.write(endpoint_code)

print("Endpoint added.")
