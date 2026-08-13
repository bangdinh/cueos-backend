import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
from api.middleware.store_context import get_store_context, StoreContext
import jwt

app = FastAPI()

@app.get("/api/some-business-route")
def some_business_route(ctx: StoreContext = Depends(get_store_context)):
    return {"status": "ok"}

@app.post("/api/auth/change-password")
def mock_change_password(ctx: StoreContext = Depends(get_store_context)):
    return {"status": "password_changed"}

client = TestClient(app)

def create_token(force_password_change: bool):
    payload = {
        "user_id": 1,
        "role": "MANAGER",
        "store_id": 1,
        "force_password_change": force_password_change
    }
    return jwt.encode(payload, "BIDA_AI_SECURE_JWT_SECRET_KEY_2026_CHANGE_IN_PROD", algorithm="HS256")

def test_middleware_blocks_if_force_true():
    token = create_token(force_password_change=True)
    response = client.get(
        "/api/some-business-route",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Vui lòng đổi mật khẩu trước khi tiếp tục." in response.json()["detail"]

def test_middleware_allows_if_force_false():
    token = create_token(force_password_change=False)
    response = client.get(
        "/api/some-business-route",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_middleware_allows_change_password_route():
    token = create_token(force_password_change=True)
    response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
