import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from .base import Base

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"

class AIEvent(Base):
    __tablename__ = "ai_events"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1, index=True)
    table_id = Column(Integer, ForeignKey("billiard_tables.id"))
    event_type = Column(String(100), index=True) # TABLE_ACTIVE, TABLE_EMPTY, HAND_RAISED
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class StaffNotification(Base):
    __tablename__ = "staff_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1, index=True)
    table_id = Column(Integer, ForeignKey("billiard_tables.id"))
    notification_type = Column(String(100))
    status = Column(String(50), default=NotificationStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
