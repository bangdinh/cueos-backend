@echo off
echo Starting Microservices...

start "Gateway (8000)" cmd /c "python -m uvicorn microservices.gateway.main:app --port 8000 --reload"
start "Auth Service (8001)" cmd /c "python -m uvicorn microservices.auth_service.main:app --port 8001 --reload"
start "Inventory Service (8002)" cmd /c "python -m uvicorn microservices.inventory_service.main:app --port 8002 --reload"
start "Billing Service (8003)" cmd /c "python -m uvicorn microservices.billing_service.main:app --port 8003 --reload"
start "Order Service (8005)" cmd /c "python -m uvicorn microservices.order_service.main:app --port 8005 --reload"

echo All services started! Check the newly opened terminal windows.
pause
