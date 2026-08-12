import os
import re

directories = ['microservices']
replacements = {
    r'db\.query\(Product\)': r'db.query(Product).filter(Product.deleted_at == None)',
    r'db\.query\(BilliardTable\)': r'db.query(BilliardTable).filter(BilliardTable.deleted_at == None)',
    r'db\.query\(UserModel\)': r'db.query(UserModel).filter(UserModel.deleted_at == None)'
}

for root, _, files in os.walk('.'):
    if 'microservices' not in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                # Avoid double replacement
                if "filter(" + old.split("(")[1].split(")")[0] + ".deleted_at == None)" not in content:
                    new_content = re.sub(old, new, new_content)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {path}")
