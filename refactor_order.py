import os

filepath = "microservices/billing_service/services/order_service.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ProductService import with httpx
content = content.replace("from services.product_service import ProductService", "import httpx\nINVENTORY_SERVICE_URL = 'http://localhost:8002'")
content = content.replace("from services.notification_service import NotificationService", "from .notification_service import NotificationService")
content = content.replace("from database.models import SessionOrderItem, PlaySession, BilliardTable", "from ..models.session import SessionOrderItem, PlaySession")

# Refactor process_customer_order
def process_order(db, table_id, items, customer_name, phone, note):
    pass
# It's better to just rewrite the file content manually because it's too complex for simple string replace.
