from typing import Optional, List, Set
from fastapi import Header, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.auth import verify_token
from database.models import UserRole
from domain.store.permissions import ALL_PERMISSIONS

security = HTTPBearer(auto_error=False)

def require_permission(permission: str, jwt_payload: dict):
    """
    Hàm helper kiểm tra quyền trực tiếp từ jwt_payload.
    Chỉ tin cậy Client Roles được Keycloak Client 'bida-app' cấp trong resource_access.
    OWNER có toàn bộ 8 permissions (theo Composite Role trên Keycloak).
    SUPER_ADMIN KHÔNG bypass — chỉ có 3 quyền view_* theo Composite Role.
    """
    client_roles = jwt_payload.get("resource_access", {}).get("bida-app", {}).get("roles", [])

    # Chỉ OWNER mới có toàn quyền (Composite Role = 8 permissions)
    if "OWNER" in client_roles:
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
        
    @property
    def is_hq(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN
        
    def has_permission(self, permission: str) -> bool:
        """Kiểm tra xem context có sở hữu permission chỉ định hay không.
        OWNER có toàn quyền (bypass). SUPER_ADMIN phải check permissions thực từ token.
        """
        if self.role == UserRole.OWNER:
            return True
        return permission in self.permissions
        
    def require_permission(self, permission: str):
        """Chặn 403 nếu không sở hữu permission yêu cầu"""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Thiếu quyền: {permission}"
            )
            
    def require_write_permission(self):
        """Kiểm tra quyền ghi, nếu là Trụ sở (HQ) sẽ từ chối 403."""
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu, không được phép ghi/sửa dữ liệu nghiệp vụ.")

    def require_admin_permission(self):
        """Kiểm tra quyền quản lý. Chỉ OWNER mới được thực hiện."""
        if self.role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Máy Mẹ (HQ) chỉ có quyền đọc dữ liệu.")
        if self.role != UserRole.OWNER and not self.has_permission("perm:manage_inventory"):
            raise HTTPException(status_code=403, detail="Chỉ OWNER hoặc người có quyền quản lý mới được thực hiện.")

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
    
    force_password_change = payload.get("force_password_change", False)
    if force_password_change and request.url.path != "/api/auth/change-password":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vui lòng đổi mật khẩu trước khi tiếp tục."
        )
    
    # 1. Trích xuất Role và Permissions CHÍNH THỐNG từ Client Roles của bida-app
    client_roles = payload.get("resource_access", {}).get("bida-app", {}).get("roles", [])
    perms = [r for r in client_roles if r.startswith("perm:")]
    
    role = None
    for r in [UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MANAGER, UserRole.STAFF]:
        if r.value in client_roles:
            role = r
            break
            
    # Fallback cho token legacy internal nếu không có client_roles
    if not role and payload.get("role"):
        try:
            role = UserRole(str(payload.get("role")).upper())
        except ValueError:
            role = UserRole.STAFF
            
    if not role:
        role = UserRole.STAFF
        
    user_id = payload.get("user_id")
    
    # Permissions được inject trực tiếp từ Composite Role của Keycloak — không fallback ALL_PERMISSIONS
    # OWNER có Composite = 8 perms, SUPER_ADMIN có Composite = 3 perms view_*
    # Nếu perms rỗng: token chưa có composite => dùng danh sách rỗng (Keycloak chưa sync)
    
    if role == UserRole.SUPER_ADMIN:
        ctx = StoreContext(store_id=None, role=role, user_id=user_id, permissions=perms)
    else:
        store_id = payload.get("store_id")
        if store_id is None:
            store_id = 1
        else:
            store_id = int(store_id)
        ctx = StoreContext(store_id=store_id, role=role, user_id=user_id, permissions=perms)
        
    request.state.store_context = ctx
    request.state.store_id = ctx.store_id
    request.state.user_role = ctx.role.value
    request.state.permissions = list(ctx.permissions)
    return ctx
