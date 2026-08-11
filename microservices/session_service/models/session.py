from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

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
    
    

