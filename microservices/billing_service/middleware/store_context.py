import jwt
from typing import Optional, List, Set
from fastapi import Header, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import enum
import os
from domain.store.permissions import ALL_PERMISSIONS

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"

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

def require_permission(permission: str, jwt_payload: dict):
    """
    Hàm helper kiểm tra quyền trực tiếp từ jwt_payload.
    Chỉ tin cậy Client Roles được Keycloak Client 'bida-app' cấp trong resource_access.
    """
    client_roles = jwt_payload.get("resource_access", {}).get("bida-app", {}).get("roles", [])
    
    if "SUPER_ADMIN" in client_roles or "OWNER" in client_roles:
        return True
        
    if permission not in client_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Thiếu quyền: {permission}"
        )
    return True

class StoreContext:
    def __init__(
        self,
        store_id: Optional[int],
        role: UserRole,
        user_id: Optional[int] = None,
        permissions: Optional[List[str]] = None
    ):
        self.store_id = store_id
        self.role = role
        self.user_id = user_id
        self.permissions: Set[str] = set(permissions or [])
        
    def has_permission(self, permission: str) -> bool:
        if self.role == UserRole.SUPER_ADMIN or self.role == UserRole.OWNER:
            return True
        return permission in self.permissions
        
    def require_permission(self, permission: str):
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Thiếu quyền: {permission}"
            )

    def require_write_permission(self):
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu, không được phép ghi/sửa dữ liệu nghiệp vụ.")

    def require_admin_permission(self):
        """Kiểm tra quyền quản lý."""
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu.")
        if self.role != UserRole.OWNER and not self.has_permission("perm:view_revenue"):
            raise HTTPException(status_code=403, detail="Chỉ OWNER hoặc người có quyền quản lý mới được thực hiện.")

def get_store_context(request: Request) -> StoreContext:
    user_id_str = request.headers.get("X-User-Id")
    role = request.headers.get("X-User-Role")
    target_store_str = request.headers.get("X-Target-Store")
    owned_stores_str = request.headers.get("X-Owned-Stores", "")
    perms_str = request.headers.get("X-User-Permissions", "")
    
    perms = [p.strip() for p in perms_str.split(",") if p.strip()] if perms_str else []

    if user_id_str and role:
        user_id = int(user_id_str)
        if role == UserRole.SUPER_ADMIN.value:
            # SUPER_ADMIN: permissions tu Composite Role cua Keycloak (3 quyen view_*)
            ctx = StoreContext(user_id=user_id, role=role, store_id=None, permissions=perms)
            request.state.store_context = ctx
            return ctx
            
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
                
        ctx = StoreContext(user_id=user_id, role=role, store_id=target_store_id, permissions=perms)
        request.state.store_context = ctx
        return ctx

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )
        
    token = auth_header.split(" ")[1].strip()
    payload = verify_token_local(token)
    
    client_roles = payload.get("resource_access", {}).get("bida-app", {}).get("roles", [])
    extracted_perms = [r for r in client_roles if r.startswith("perm:")]
    
    role_enum = None
    for r in [UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER, UserRole.STAFF]:
        if r.value in client_roles:
            role_enum = r
            break
            
    if not role_enum and payload.get("role"):
        try:
            role_enum = UserRole(str(payload.get("role")).upper())
        except ValueError:
            role_enum = UserRole.STAFF
            
    if not role_enum:
        role_enum = UserRole.STAFF
        
    user_id = payload.get("user_id", 1)
    
    # Permissions tu Composite Role cua Keycloak — khong fallback ALL_PERMISSIONS
    # SUPER_ADMIN: 3 perms view_*, OWNER: 8 perms day du
        
    if role_enum == UserRole.SUPER_ADMIN:
        ctx = StoreContext(store_id=None, role=role_enum, user_id=user_id, permissions=extracted_perms)
    else:
        store_id = payload.get("store_id", 1)
        ctx = StoreContext(store_id=int(store_id), role=role_enum, user_id=user_id, permissions=extracted_perms)
        
    request.state.store_context = ctx
    request.state.store_id = ctx.store_id
    request.state.user_role = ctx.role.value if hasattr(ctx.role, "value") else str(ctx.role)
    return ctx
