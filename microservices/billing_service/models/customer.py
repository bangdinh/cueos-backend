from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import Column, Integer, String, DateTime
from .base import Base

class CustomerModel(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, default=1, index=True) # If null, belongs to HQ/System
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
