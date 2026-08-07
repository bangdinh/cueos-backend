from sqlalchemy import Column, Integer, String
from database.models.base import Base

class StoreModel(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    address = Column(String(255), default="")
    phone = Column(String(20), default="")
    status = Column(String(50), default="ACTIVE")
