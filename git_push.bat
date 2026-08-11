@echo off
git init
git remote remove origin 2>nul
git remote add origin https://github.com/bangdinh/cueos-backend
git checkout dev 2>nul
if %errorlevel% neq 0 (
    git checkout -b dev
)
git checkout -b refactor/CUEOS-001-microservices-architecture
git add .
git commit -m "[CUEOS-001] refactor(microservices): migrate monolithic system to 4 microservices (gateway, auth, inventory, billing)"
git push -u origin refactor/CUEOS-001-microservices-architecture
