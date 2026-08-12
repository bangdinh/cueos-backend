import os
import glob
import shutil

for svc in ["session_service", "order_service"]:
    base_dir = f"microservices/{svc}/models"
    models_models_dir = os.path.join(base_dir, "models")
    
    # If models/models exists, move all files up
    if os.path.exists(models_models_dir):
        for f in os.listdir(models_models_dir):
            src = os.path.join(models_models_dir, f)
            dst = os.path.join(base_dir, f)
            if os.path.isfile(src):
                shutil.move(src, dst)
        shutil.rmtree(models_models_dir)
        
    # Replace imports
    for p in glob.glob(f"{base_dir}/*.py"):
        with open(p, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Only replace if it contains the old monolithic base import
        if "from database.models.base import Base" in content:
            new_content = content.replace("from database.models.base import Base", "from .base import Base")
            with open(p, "w", encoding="utf-8") as file:
                file.write(new_content)
        
print("Done fixing models")
