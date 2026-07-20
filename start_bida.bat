@echo off
echo Dang khoi dong He Thong Bida AI...
cd /d "%~dp0"
start "Bida API Server" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8888 --workers 4"
start "Bida AI Workers" cmd /k "python run_workers.py"
echo He thong da chay thanh cong!
