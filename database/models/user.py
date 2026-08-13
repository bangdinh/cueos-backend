import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import validates
from database.models.base import Base
from datetime import datetime

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"

class UserStoreRole(Base):
    __tablename__ = "user_store_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'store_id', name='uq_user_store'),
    )

    @validates('role')
    def validate_role(self, key, role):
        allowed_roles = {UserRole.OWNER.value, UserRole.MANAGER.value, UserRole.STAFF.value, UserRole.SUPER_ADMIN.value}
        if role not in allowed_roles:
            raise ValueError(f"Invalid role: {role}")
        return role

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Security columns
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    force_password_change = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
