import re

def replace_in_file(filepath, pattern, replacement):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(pattern, replacement, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file("microservices/auth_service/main.py", r'prefix="/api/auth", ', '')
replace_in_file("microservices/inventory_service/main.py", r'prefix="/api/products", ', '')
replace_in_file("microservices/inventory_service/main.py", r'prefix="/api/tables", ', '')
replace_in_file("microservices/billing_service/main.py", r'prefix="/api/session", ', '')
replace_in_file("microservices/billing_service/main.py", r'prefix="/api/reports", ', '')

print("Fixed prefixes in main.py files.")
