@echo off
echo ============================================================
echo  Khoi dong Keycloak 26.7.1 - bida-realm
echo  Admin Console : http://localhost:8080/admin
echo  OIDC Endpoint : http://localhost:8080/realms/bida-realm
echo ============================================================
echo.

set KC_HOME=D:\keycloak-26.7.1\keycloak-26.7.1

if not exist "%KC_HOME%\lib\quarkus-run.jar" (
    echo [LOI] Khong tim thay Keycloak tai: %KC_HOME%
    echo       Kiem tra lai duong dan trong file nay.
    pause
    exit /b 1
)

echo [INFO] Keycloak dang khoi dong, vui long cho...
echo [INFO] Nhan Ctrl+C de dung Keycloak.
echo.

cd /d "%KC_HOME%"
java "-Dkc.home.dir=." "-Dkc.config.built=true" -cp ".\lib\quarkus-run.jar" io.quarkus.bootstrap.runner.QuarkusEntryPoint start-dev
