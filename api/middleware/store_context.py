from typing import Optional
from fastapi import Header, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.auth import verify_token
from database.models import UserRole

security = HTTPBearer(auto_error=False)

class StoreContext:
    def __init__(self, store_id: Optional[int], role: UserRole, user_id: Optional[int] = None):
        self.store_id = store_id
        self.role = role
        self.user_id = user_id
        
    @property
    def is_hq(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN
        
    def require_write_permission(self):
        """Kiểm tra quyền ghi, nếu là Trụ sở (HQ) sẽ từ chối 403."""
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu, không được phép ghi/sửa dữ liệu nghiệp vụ.")

    def require_admin_permission(self):
        """Kiểm tra quyền quản lý. Chỉ ADMIN mới được thực hiện. MANAGER và SUPER_ADMIN đều bị từ chối."""
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
    
    payload = verify_token(token)
    
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
        if store_id is None:
            store_id = 1
        else:
            store_id = int(store_id)
        ctx = StoreContext(store_id=store_id, role=role, user_id=user_id)
        
    request.state.store_context = ctx
    request.state.store_id = ctx.store_id
    request.state.user_role = ctx.role.value
    return ctx
