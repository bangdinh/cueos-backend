from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, default=1, index=True)
    name = Column(String(100), index=True, nullable=False)
    price = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    category = Column(String(50))
    image_url = Column(String(255), default="")
    
    order_items = relationship("SessionOrderItem", back_populates="product")
