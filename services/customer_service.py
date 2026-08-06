from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import CustomerModel

class CustomerService:
    @staticmethod
    def get_customer_by_phone(db: Session, phone: str) -> Optional[CustomerModel]:
        """Lấy thông tin khách hàng bằng số điện thoại."""
        return db.query(CustomerModel).filter(CustomerModel.phone == phone).first()

    @staticmethod
    def get_customer_by_id(db: Session, customer_id: int) -> Optional[CustomerModel]:
        """Lấy thông tin khách hàng bằng ID."""
        return db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()

    @staticmethod
    def get_customers_by_store(db: Session, store_id: int) -> List[CustomerModel]:
        """Lấy danh sách khách hàng của một chi nhánh cụ thể."""
        return db.query(CustomerModel).filter(CustomerModel.store_id == store_id).all()

    @staticmethod
    def create_or_update_customer(db: Session, name: str, phone: str, store_id: Optional[int] = None) -> CustomerModel:
        """Tạo mới hoặc cập nhật thông tin khách hàng nếu đã tồn tại."""
        customer = CustomerService.get_customer_by_phone(db, phone)
        if customer:
            customer.name = name
            if store_id is not None:
                customer.store_id = store_id
        else:
            customer = CustomerModel(name=name, phone=phone, store_id=store_id)
            db.add(customer)
        
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def add_points(db: Session, customer_id: int, points: int) -> Optional[CustomerModel]:
        """Tích lũy điểm cho khách hàng."""
        customer = CustomerService.get_customer_by_id(db, customer_id)
        if customer:
            customer.points += points
            db.commit()
            db.refresh(customer)
        return customer
