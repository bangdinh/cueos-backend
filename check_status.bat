@echo off
echo ==============================================
echo KIEM TRA TRANG THAI CAC MICROSERVICES
echo ==============================================
echo.

echo [1] Kiem tra API Gateway (Port 8000)...
curl -s -o nul -w "Trang thai: HTTP %%{http_code}\n" http://127.0.0.1:8000/docs
echo.

echo [2] Kiem tra Auth Service (Port 8001)...
curl -s -o nul -w "Trang thai: HTTP %%{http_code}\n" http://127.0.0.1:8001/docs
echo.

echo [3] Kiem tra Inventory Service (Port 8002)...
curl -s -o nul -w "Trang thai: HTTP %%{http_code}\n" http://127.0.0.1:8002/docs
echo.

echo [4] Kiem tra Billing Service (Port 8003)...
curl -s -o nul -w "Trang thai: HTTP %%{http_code}\n" http://127.0.0.1:8003/docs
echo.

echo [5] Kiem tra Order Service (Port 8005)...
curl -s -o nul -w "Trang thai: HTTP %%{http_code}\n" http://127.0.0.1:8005/docs
echo.

echo [6] Kiem tra Session Service (Port 8006)...
curl -s -o nul -w "Trang thai: HTTP %%{http_code}\n" http://127.0.0.1:8006/docs
echo.

echo ==============================================
echo Neu tat ca tra ve "HTTP 200", he thong cua ban dang hoat dong hoan hao!
echo ==============================================
pause
