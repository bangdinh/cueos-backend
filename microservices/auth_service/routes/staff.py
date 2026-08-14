import string
import random
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict

from .auth import get_current_user
from ..database import get_db
from database.models.user import UserModel, UserStoreRole, UserRole
from domain.store.value_objects import Role, can_assign_role

router = APIRouter(prefix="/api/stores", tags=["Staff Management"])

class CreateStaffRequest(BaseModel):
    phone: str
    full_name: str
    role: str

class CreateStaffResponse(BaseModel):
    user_id: int
    phone: str
    temp_password: str

def generate_temp_password(length: int = 8) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@router.post("/{store_id}/staff", response_model=CreateStaffResponse)
def create_staff(
    store_id: int, 
    req: CreateStaffRequest, 
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assigner_role_str = None
    
    # Extract assigner role for this specific store_id from JWT payload
    if current_user.get("role") == UserRole.SUPER_ADMIN.value:
        assigner_role_str = UserRole.SUPER_ADMIN.value
    else:
        for sr in current_user.get("store_roles", []):
            if sr.get("store_id") == store_id:
                assigner_role_str = sr.get("role")
                break
                
    if not assigner_role_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"You do not have a role in store {store_id}"
        )
        
    # Check permission if caller has custom role permissions
    client_roles = current_user.get("resource_access", {}).get("bida-app", {}).get("roles", [])
    realm_roles = current_user.get("realm_access", {}).get("roles", [])
    perms = [r for r in client_roles + realm_roles if r.startswith("perm:")]
    if perms and "perm:manage_staff" not in perms and assigner_role_str != UserRole.OWNER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Thiếu quyền: perm:manage_staff")

    try:
        assigner_role_enum = Role(assigner_role_str)
        target_role_enum = Role(req.role.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role specified")
        
    if not can_assign_role(assigner_role_enum, target_role_enum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Role {assigner_role_enum.value} cannot assign {target_role_enum.value}"
        )
        
    temp_password = generate_temp_password()
    
    try:
        # Atomic transaction
        # 1. Create User
        new_user = UserModel(
            username=req.phone,  # Use phone as username
            password_hash=temp_password,
            force_password_change=True,
            created_by=current_user.get("user_id")
        )
        db.add(new_user)
        db.flush()  # To get new_user.id
        
        # 2. Assign Store Role
        new_user_store_role = UserStoreRole(
            user_id=new_user.id,
            store_id=store_id,
            role=target_role_enum.value
        )
        db.add(new_user_store_role)
        
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username (phone) already exists or store does not exist"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to create staff account"
        )

    return CreateStaffResponse(
        user_id=new_user.id,
        phone=req.phone,
        temp_password=temp_password
    )
