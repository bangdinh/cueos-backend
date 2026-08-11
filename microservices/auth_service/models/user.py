import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from .base import Base

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OWNER = "OWNER"
    STORE_MANAGER = "STORE_MANAGER"
    CASHIER = "CASHIER"

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    full_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True, unique=True)
    role = Column(String(50), nullable=False, default=UserRole.CASHIER.value)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
