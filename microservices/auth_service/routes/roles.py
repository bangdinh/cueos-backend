from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from ..database import get_db
from ..keycloak_auth import get_current_keycloak_user
from ..keycloak_admin import (
    get_client_uuid,
    get_client_roles,
    get_role_composites,
    create_custom_composite_role
)
from domain.store.permissions import (
    get_all_permissions_metadata,
    ALL_PERMISSIONS,
    is_valid_permission
)
from database.models import UserModel, UserStoreRole, UserRole

router = APIRouter(tags=["Roles & Permissions"])

class CreateCustomRoleRequest(BaseModel):
    role_name: str = Field(..., min_length=2, max_length=50, description="Tên định danh của role (vd: CASHIER_ORDER)")
    display_name: str = Field(..., min_length=2, max_length=100, description="Tên hiển thị (vd: Thu ngân kiêm Order)")
    permissions: List[str] = Field(..., min_length=1, description="Danh sách các mã quyền perm:*")

class CustomRoleResponse(BaseModel):
    role_name: str
    display_name: str
    permissions: List[str]
    store_id: int

@router.get("/api/permissions")
def list_permissions():
    """
    Trả về danh mục toàn bộ Permission hạt nhân chuẩn của hệ thống kèm mô tả tiếng Việt.
    (Phục vụ UI cấu hình phân quyền).
    """
    return {
        "status": "success",
        "permissions": get_all_permissions_metadata()
    }

def _get_caller_permissions(user_payload: Dict, is_owner: bool) -> set:
    """Trích xuất tập hợp các permissions mà caller đang sở hữu từ JWT token.
    OWNER (is_owner=True) có toàn bộ 8 permissions.
    SUPER_ADMIN KHÔNG bypass — chỉ có permissions thực từ Composite Role Keycloak (3 quyền view_*).
    """
    client_roles = user_payload.get("resource_access", {}).get("bida-app", {}).get("roles", [])

    # Chỉ OWNER thật sự có toàn quyền (Composite = 8 permissions)
    if "OWNER" in client_roles or is_owner:
        return set(ALL_PERMISSIONS)

    # Với mọi role khác (kể cả SUPER_ADMIN): chỉ nhận permissions thực từ token
    caller_perms = {r for r in client_roles if r.startswith("perm:")}
    return caller_perms

@router.post("/api/stores/{store_id}/roles", response_model=CustomRoleResponse)
def create_store_custom_role(
    store_id: int,
    req: CreateCustomRoleRequest,
    user: Dict = Depends(get_current_keycloak_user),
    db: Session = Depends(get_db)
):
    """
    Cho phép OWNER của chi nhánh tự tạo Custom Role dạng Composite Roles trên Keycloak.
    
    Bảo vệ & Ràng buộc:
    1. Xác thực người gọi có quyền OWNER tại store_id này (tra cứu qua auth.db).
    2. Validate danh sách permissions gửi lên phải là tập con của ALL_PERMISSIONS chuẩn.
    3. Guard: Caller không được gán quyền vượt quá các quyền caller đang sở hữu.
    4. Rollback Keycloak nếu có lỗi giữa chừng khi gán composite permissions.
    """
    username = user.get("preferred_username")
    client_roles = user.get("resource_access", {}).get("bida-app", {}).get("roles", [])
    realm_roles = user.get("realm_access", {}).get("roles", [])
    
    # 1. Kiểm tra quyền OWNER tại store_id này trong auth.db
    is_authorized = False
    is_owner = False
    
    # Nếu là SUPER_ADMIN trên Keycloak Client Roles hoặc Realm Roles
    if "SUPER_ADMIN" in client_roles or "SUPER_ADMIN" in realm_roles:
        is_authorized = True
        is_owner = True
    else:
        # Tìm user trong auth.db
        user_record = db.query(UserModel).filter(UserModel.username == username).first()
        if user_record:
            store_role = db.query(UserStoreRole).filter(
                UserStoreRole.user_id == user_record.id,
                UserStoreRole.store_id == store_id,
                UserStoreRole.role.in_([UserRole.OWNER.value, "OWNER"])
            ).first()
            if store_role:
                is_authorized = True
                is_owner = True

    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Chỉ OWNER của chi nhánh {store_id} mới có quyền tạo Custom Role"
        )

    # 2. Validate mã permission gửi lên
    invalid_perms = [p for p in req.permissions if not is_valid_permission(p)]
    if invalid_perms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Danh sách chứa permission không hợp lệ: {invalid_perms}. Chỉ chấp nhận các mã perm:* chuẩn."
        )

    # 3. Guard: Caller không được gán quyền vượt quá các quyền caller đang sở hữu
    caller_perms = _get_caller_permissions(user, is_owner=is_owner)
    unauthorized_perms = [p for p in req.permissions if p not in caller_perms]
    if unauthorized_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Bạn không thể gán các quyền mà chính bạn không sở hữu: {unauthorized_perms}"
        )

    # 4. Định dạng tên Role (chuẩn hóa theo store để tránh xung đột giữa các chi nhánh)
    clean_role_name = req.role_name.strip().upper().replace(" ", "_")
    scoped_role_name = f"STORE_{store_id}_{clean_role_name}" if not clean_role_name.startswith(f"STORE_{store_id}_") else clean_role_name
    
    # 5. Gọi Keycloak Admin API tạo Custom Role kèm composite permissions
    try:
        res = create_custom_composite_role(
            role_name=scoped_role_name,
            display_name=f"{req.display_name} (Chi nhánh {store_id})",
            permissions=req.permissions,
            client_name="bida-app"
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi Keycloak Admin API: {str(e)}")

    return CustomRoleResponse(
        role_name=scoped_role_name,
        display_name=req.display_name,
        permissions=req.permissions,
        store_id=store_id
    )

@router.get("/api/stores/{store_id}/roles")
def list_store_custom_roles(
    store_id: int,
    user: Dict = Depends(get_current_keycloak_user),
    db: Session = Depends(get_db)
):
    """
    Liệt kê toàn bộ Custom Role và các permission đi kèm đã tạo cho chi nhánh store_id.
    """
    try:
        client_uuid = get_client_uuid("bida-app")
        all_roles = get_client_roles(client_uuid)
        
        store_prefix = f"STORE_{store_id}_"
        store_roles = []
        
        for r in all_roles:
            role_name = r.get("name", "")
            if role_name.startswith(store_prefix):
                # Lấy composite permissions của role này
                composites = get_role_composites(client_uuid, role_name)
                perm_names = [c["name"] for c in composites if c.get("name", "").startswith("perm:")]
                
                store_roles.append({
                    "role_name": role_name,
                    "display_name": r.get("description", role_name),
                    "permissions": perm_names,
                    "store_id": store_id
                })
                
        return {
            "status": "success",
            "store_id": store_id,
            "roles": store_roles
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể lấy danh sách role từ Keycloak: {str(e)}"
        )
