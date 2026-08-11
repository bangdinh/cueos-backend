import re

def replace_in_file(filepath, pattern, replacement):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(pattern, replacement, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

inv_tables = "microservices/inventory_service/routes/tables.py"
replace_in_file(inv_tables, r"# Store context disabled for now", "from ..middleware.store_context import StoreContext, get_store_context\nfrom fastapi import Depends")

bill_sessions = "microservices/billing_service/routes/sessions.py"
replace_in_file(bill_sessions, r"# Store context disabled for now", "from ..middleware.store_context import StoreContext, get_store_context\nfrom fastapi import Depends")

bill_reports = "microservices/billing_service/routes/reports.py"
replace_in_file(bill_reports, r"# Store context disabled for now", "from ..middleware.store_context import StoreContext, get_store_context\nfrom fastapi import Depends")

print("Restored store context imports.")
