from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from .base import Base

class SessionOrderItem(Base):
    __tablename__ = "session_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, default=1, index=True)
    session_id = Column(Integer, index=True) # Logical foreign key to Session Service
    product_id = Column(Integer, nullable=True) # Logical foreign key to Inventory Service
    item_name = Column(String(100))
    quantity = Column(Integer, default=1)
    price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
