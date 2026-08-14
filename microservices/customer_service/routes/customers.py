from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..keycloak_auth import require_customer_role
from database.models.customer import CustomerModel

router = APIRouter(tags=["Customers"])

# ================= Schemas =================
class CustomerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    store_id: Optional[int] = None
    points: Optional[int] = 0

class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    store_id: Optional[int] = None

class AddPointsRequest(BaseModel):
    points_delta: int = Field(..., description="Số điểm cộng (+) hoặc trừ (-)")
    reason: Optional[str] = None

class UpdateProfileRequest(BaseModel):
    phone: Optional[str] = None
    store_id: Optional[int] = None

# ================= CRM Endpoints =================

@router.get("/api/customers/{id}")
def get_customer_by_id(id: int, db: Session = Depends(get_db)):
    """Lấy thông tin khách hàng theo ID"""
    customer = db.query(CustomerModel).filter(CustomerModel.id == id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách hàng với ID {id}"
        )
    return customer

@router.get("/api/customers")
def list_customers(
    store_id: Optional[int] = Query(None, description="Lọc theo chi nhánh"),
    phone: Optional[str] = Query(None, description="Lọc theo số điện thoại"),
    db: Session = Depends(get_db)
):
    """Tìm kiếm khách hàng theo store_id hoặc số điện thoại"""
    query = db.query(CustomerModel)
    if phone:
        query = query.filter(CustomerModel.phone == phone)
    if store_id:
        query = query.filter(CustomerModel.store_id == store_id)
        
    return query.all()

@router.post("/api/customers", status_code=status.HTTP_201_CREATED)
def create_customer(req: CustomerCreateRequest, db: Session = Depends(get_db)):
    """Tạo mới hồ sơ khách hàng"""
    if req.phone:
        existing = db.query(CustomerModel).filter(CustomerModel.phone == req.phone).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số điện thoại này đã tồn tại trong hệ thống"
            )
            
    customer = CustomerModel(
        name=req.name,
        phone=req.phone,
        store_id=req.store_id,
        points=req.points or 0
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.put("/api/customers/{id}")
def update_customer(id: int, req: CustomerUpdateRequest, db: Session = Depends(get_db)):
    """Cập nhật thông tin khách hàng"""
    customer = db.query(CustomerModel).filter(CustomerModel.id == id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách hàng với ID {id}"
        )
        
    if req.phone and req.phone != customer.phone:
        existing = db.query(CustomerModel).filter(CustomerModel.phone == req.phone, CustomerModel.id != id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số điện thoại này đã được sử dụng bởi khách hàng khác"
            )
        customer.phone = req.phone
        
    if req.name is not None:
        customer.name = req.name
    if req.store_id is not None:
        customer.store_id = req.store_id
        
    db.commit()
    db.refresh(customer)
    return customer

@router.put("/api/customers/{id}/points")
def modify_customer_points(id: int, req: AddPointsRequest, db: Session = Depends(get_db)):
    """Cộng hoặc trừ điểm tích lũy của khách hàng"""
    customer = db.query(CustomerModel).filter(CustomerModel.id == id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khách hàng với ID {id}"
        )
        
    new_points = customer.points + req.points_delta
    if new_points < 0:
        new_points = 0
        
    customer.points = new_points
    db.commit()
    db.refresh(customer)
    
    return {
        "status": "success",
        "customer_id": customer.id,
        "points_delta": req.points_delta,
        "current_points": customer.points,
        "reason": req.reason
    }

# ================= Customer Portal Endpoints =================

@router.get("/api/customer/me")
def get_customer_profile(
    user: Dict = Depends(require_customer_role),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin hồ sơ khách hàng.
    Nếu khách hàng đăng nhập lần đầu qua Keycloak, tự động tạo bản ghi trong customer.db.
    """
    username = user.get("preferred_username") or "khachhang"
    email = user.get("email")
    sub = user.get("sub")
    
    customer = db.query(CustomerModel).filter(CustomerModel.name == username).first()
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

@router.put("/api/customer/profile")
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

@router.get("/api/customer/points")
def get_loyalty_points(
    user: Dict = Depends(require_customer_role),
    db: Session = Depends(get_db)
):
    """Kiểm tra điểm thưởng và hạng thành viên của khách hàng"""
    username = user.get("preferred_username")
    customer = db.query(CustomerModel).filter(CustomerModel.name == username).first()
    points = customer.points if customer else 0
    
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
