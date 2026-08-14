from typing import Optional, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..keycloak_auth import require_customer_role, get_current_keycloak_user
from database.models import CustomerModel

router = APIRouter(prefix="/api/customer", tags=["Customer Portal"])

class UpdateProfileRequest(BaseModel):
    phone: Optional[str] = None
    store_id: Optional[int] = None

@router.get("/me")
def get_customer_profile(
    user: Dict = Depends(require_customer_role),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin hồ sơ khách hàng.
    Nếu khách hàng đăng nhập lần đầu qua Keycloak, tự động đồng bộ hồ sơ vào auth.db.
    """
    username = user.get("preferred_username") or "khachhang"
    email = user.get("email")
    sub = user.get("sub")
    
    # Tìm kiếm khách hàng theo name/username trong auth.db
    customer = db.query(CustomerModel).filter(CustomerModel.name == username).first()
    
    # Tự động tạo hồ sơ khách hàng nếu chưa tồn tại trong auth.db
    if not customer:
        customer = CustomerModel(
            name=username,
            phone=None,
            points=0,
            store_id=None
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
    return {
        "status": "success",
        "keycloak_sub": sub,
        "username": username,
        "email": email,
        "customer_id": customer.id,
        "phone": customer.phone,
        "points": customer.points,
        "store_id": customer.store_id,
        "created_at": customer.created_at
    }

@router.put("/profile")
def update_customer_profile(
    req: UpdateProfileRequest,
    user: Dict = Depends(require_customer_role),
    db: Session = Depends(get_db)
):
    """Cập nhật số điện thoại hoặc chi nhánh thân thiết của khách hàng"""
    username = user.get("preferred_username")
    customer = db.query(CustomerModel).filter(CustomerModel.name == username).first()
    
    if not customer:
        customer = CustomerModel(
            name=username,
            phone=req.phone,
            store_id=req.store_id,
            points=0
        )
        db.add(customer)
    else:
        if req.phone is not None:
            # Kiểm tra xem phone đã có ai đăng ký chưa
            existing = db.query(CustomerModel).filter(CustomerModel.phone == req.phone, CustomerModel.id != customer.id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Số điện thoại này đã được sử dụng bởi khách hàng khác"
                )
            customer.phone = req.phone
        if req.store_id is not None:
            customer.store_id = req.store_id
            
    db.commit()
    db.refresh(customer)
    
    return {
        "status": "success",
        "message": "Cập nhật hồ sơ thành công",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "points": customer.points,
            "store_id": customer.store_id
        }
    }

@router.get("/points")
def get_loyalty_points(
    user: Dict = Depends(require_customer_role),
    db: Session = Depends(get_db)
):
    """Kiểm tra điểm thưởng và hạng thành viên của khách hàng"""
    username = user.get("preferred_username")
    customer = db.query(CustomerModel).filter(CustomerModel.name == username).first()
    points = customer.points if customer else 0
    
    # Tính hạng thành viên dựa trên điểm
    tier = "BRONZE"
    if points >= 1000:
        tier = "DIAMOND"
    elif points >= 500:
        tier = "GOLD"
    elif points >= 200:
        tier = "SILVER"
        
    return {
        "status": "success",
        "username": username,
        "points": points,
        "tier": tier
    }
