import subprocess
import time
import httpx
import sys
import psutil

def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)

print("Starting 4 microservices...")
p1 = subprocess.Popen([sys.executable, "-m", "uvicorn", "microservices.gateway.main:app", "--port", "8000"])
p2 = subprocess.Popen([sys.executable, "-m", "uvicorn", "microservices.auth_service.main:app", "--port", "8001"])
p3 = subprocess.Popen([sys.executable, "-m", "uvicorn", "microservices.inventory_service.main:app", "--port", "8002"])
p4 = subprocess.Popen([sys.executable, "-m", "uvicorn", "microservices.billing_service.main:app", "--port", "8003"])

try:
    print("Waiting for servers to boot (5 seconds)...")
    time.sleep(5)
    
    print("\n--- Test 1: Testing Gateway -> Auth Service ---")
    try:
        res1 = httpx.post("http://127.0.0.1:8000/api/auth/login", json={"username": "wrong", "password": "wrong"}, timeout=5)
        print("Response Code:", res1.status_code)
    except Exception as e:
        print("Test 1 Failed:", e)

    print("\n--- Test 2: Testing Gateway -> Inventory Service ---")
    try:
        res2 = httpx.get("http://127.0.0.1:8000/api/tables", timeout=5)
        print("Response Code:", res2.status_code)
    except Exception as e:
        print("Test 2 Failed:", e)
        
    print("\n--- Test 3: Testing Gateway -> Billing Service ---")
    try:
        res3 = httpx.get("http://127.0.0.1:8000/api/history", timeout=5)
        print("Response Code:", res3.status_code)
    except Exception as e:
        print("Test 3 Failed:", e)
finally:
    print("\nCleaning up processes...")
    try: kill_proc_tree(p1.pid)
    except: pass
    try: kill_proc_tree(p2.pid)
    except: pass
    try: kill_proc_tree(p3.pid)
    except: pass
    try: kill_proc_tree(p4.pid)
    except: pass
    print("Done testing.")
