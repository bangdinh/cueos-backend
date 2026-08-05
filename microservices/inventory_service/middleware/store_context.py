import jwt
from typing import Optional
from fastapi import Header, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import enum
import os

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "BIDA_AI_SECURE_JWT_SECRET_KEY_2026_CHANGE_IN_PROD")
JWT_ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

def verify_token_local(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token đã hết hạn")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")

class StoreContext:
    def __init__(self, store_id: Optional[int], role: UserRole, user_id: Optional[int] = None):
        self.store_id = store_id
        self.role = role
        self.user_id = user_id
        
    def require_write_permission(self):
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu, không được phép ghi/sửa dữ liệu nghiệp vụ.")

    def require_admin_permission(self):
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu.")
        if self.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Chỉ ADMIN của chi nhánh mới có quyền thực hiện hành động này.")

def get_store_context(
    request: Request,
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> StoreContext:
    token = None
    if auth_credentials and auth_credentials.credentials:
        token = auth_credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        
    if token:
        token = token.split(",")[0].replace("Bearer ", "").strip()
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token_local(token)
    
    role_str = str(payload.get("role", "MANAGER")).upper()
    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.MANAGER
        
    user_id = payload.get("user_id")
    
    if role == UserRole.SUPER_ADMIN:
        ctx = StoreContext(store_id=None, role=role, user_id=user_id)
    else:
        store_id = payload.get("store_id")
        ctx = StoreContext(store_id=int(store_id) if store_id else 1, role=role, user_id=user_id)
        
    request.state.store_context = ctx
    request.state.store_id = ctx.store_id
    request.state.user_role = ctx.role.value
    return ctx
