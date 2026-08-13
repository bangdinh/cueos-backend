import jwt
from typing import Optional
from fastapi import Header, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import enum
import os

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OWNER = "OWNER"
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
        """Kiểm tra quyền quản lý. Chỉ OWNER mới được thực hiện. MANAGER và SUPER_ADMIN đều bị từ chối."""
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu.")
        if self.role != UserRole.OWNER:
            raise HTTPException(status_code=403, detail="Chỉ OWNER của chi nhánh mới có quyền thực hiện hành động này.")

def get_store_context(request: Request) -> StoreContext:
    """
    Lấy context từ headers (được API Gateway hoặc Auth Service validate).
    """
    user_id_str = request.headers.get("X-User-Id")
    role = request.headers.get("X-User-Role")
    target_store_str = request.headers.get("X-Target-Store")
    owned_stores_str = request.headers.get("X-Owned-Stores", "")
    
    if not user_id_str or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers"
        )
        
    user_id = int(user_id_str)
    
    if role == UserRole.SUPER_ADMIN.value:
        return StoreContext(
            user_id=user_id,
            role=role,
            store_id=None
        )
        
    if not target_store_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Target-Store header for non-HQ user"
        )
        
    target_store_id = int(target_store_str)
    
    if role == UserRole.OWNER.value:
        owned_ids = []
        if owned_stores_str:
            try:
                owned_ids = [int(x.strip()) for x in owned_stores_str.split(',') if x.strip()]
            except ValueError:
                pass
        if target_store_id not in owned_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Owner does not have access to store {target_store_id}"
            )
    else:
        auth_store_str = request.headers.get("X-Store-Id")
        if not auth_store_str or int(auth_store_str) != target_store_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-store access denied"
            )
            
    return StoreContext(
        user_id=user_id,
        role=role,
        store_id=target_store_id
    )


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
