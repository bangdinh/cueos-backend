import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from database.models.base import Base
from datetime import datetime

class TableStatus(str, enum.Enum):
    EMPTY = "EMPTY"
    PLAYING = "PLAYING"
    MAINTENANCE = "MAINTENANCE"

class BilliardTable(Base):
    __tablename__ = "billiard_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, default=1, index=True)
    name = Column(String(100), index=True)
    camera_url = Column(String(255))
    current_status = Column(String(50), default=TableStatus.EMPTY.value)
    price_per_hour = Column(Float, default=50000.0)
    table_tier = Column(String(50), default="STANDARD")
    table_type = Column(String(50), default="LIP")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
