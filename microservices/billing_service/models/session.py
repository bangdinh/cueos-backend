from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class PlaySession(Base):
    __tablename__ = "play_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, default=1)
    table_id = Column(Integer, index=True) # Soft reference to Inventory Service
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_minutes = Column(Integer, default=0)
    play_fee = Column(Float, default=0.0)
    services_fee = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    status = Column(String(50), default="ACTIVE", index=True) # ACTIVE, COMPLETED
    is_synced_to_hq = Column(Boolean, default=False, index=True)
    
    order_items = relationship("SessionOrderItem", back_populates="session", cascade="all, delete-orphan")

class SessionOrderItem(Base):
    __tablename__ = "session_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, default=1, index=True)
    session_id = Column(Integer, ForeignKey("play_sessions.id"))
    product_id = Column(Integer, nullable=True, index=True)
    item_name = Column(String(100))
    quantity = Column(Integer, default=1)
    price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    session = relationship("PlaySession", back_populates="order_items")
