from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import validates
from database.models.user import UserRole
from database.models.base import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(Integer, nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StaffInvitation(Base):
    __tablename__ = "staff_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    role = Column(String(50), nullable=False)
    token = Column(String(255), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @validates('role')
    def validate_role(self, key, role):
        allowed_roles = {UserRole.OWNER.value, UserRole.MANAGER.value, UserRole.STAFF.value}
        if role not in allowed_roles:
            raise ValueError(f"Invalid role: {role}")
        return role
