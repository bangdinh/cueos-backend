from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.models.base import Base

class PlaySession(Base):
    __tablename__ = "play_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1, index=True)
    table_id = Column(Integer, ForeignKey("billiard_tables.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_minutes = Column(Integer, default=0)
    play_fee = Column(Float, default=0.0)
    services_fee = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    status = Column(String(50), default="ACTIVE", index=True) # ACTIVE, COMPLETED
    is_synced_to_hq = Column(Boolean, default=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order_items = relationship("SessionOrderItem", back_populates="session", cascade="all, delete-orphan")

class SessionOrderItem(Base):
    __tablename__ = "session_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1, index=True)
    session_id = Column(Integer, ForeignKey("play_sessions.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    item_name = Column(String(100))
    quantity = Column(Integer, default=1)
    price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = relationship("PlaySession", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
