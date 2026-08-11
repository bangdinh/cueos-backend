import os
import re

def replace_in_file(filepath, pattern, replacement):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(pattern, replacement, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Fix Inventory Service
inv_tables = "microservices/inventory_service/routes/tables.py"
replace_in_file(inv_tables, r"from database\.database import SessionLocal", "from ..database import SessionLocal")
replace_in_file(inv_tables, r"from database\.models import BilliardTable, Product", "from ..models.billiard_table import BilliardTable\nfrom ..models.product import Product")
replace_in_file(inv_tables, r"from api\.middleware\.store_context import.*", "# Store context disabled for now")
replace_in_file(inv_tables, r"from api\.websocket_server import websocket_manager", "# WS disabled")

# Fix Billing Service
bill_sessions = "microservices/billing_service/routes/sessions.py"
replace_in_file(bill_sessions, r"from database\.database import SessionLocal", "from ..database import SessionLocal")
replace_in_file(bill_sessions, r"from database\.models import.*", "from ..models.session import PlaySession, SessionOrderItem")
replace_in_file(bill_sessions, r"from api\.middleware\.store_context import.*", "# Store context disabled for now")
replace_in_file(bill_sessions, r"from api\.websocket_server import websocket_manager", "# WS disabled")

bill_reports = "microservices/billing_service/routes/reports.py"
replace_in_file(bill_reports, r"from database\.database import SessionLocal", "from ..database import SessionLocal")
replace_in_file(bill_reports, r"from database\.models import.*", "from ..models.session import PlaySession, SessionOrderItem")
replace_in_file(bill_reports, r"from api\.middleware\.store_context import.*", "# Store context disabled for now")
replace_in_file(bill_reports, r"from api\.websocket_server import websocket_manager", "# WS disabled")

print("Imports refactored.")
