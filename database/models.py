from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TableStatus(str, enum.Enum):
    EMPTY = "EMPTY"
    PLAYING = "PLAYING"
    MAINTENANCE = "MAINTENANCE"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"

class BilliardTable(Base):
    __tablename__ = "billiard_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    camera_url = Column(String(255))
    current_status = Column(String(50), default=TableStatus.EMPTY.value)
    price_per_hour = Column(Float, default=50000.0) # Giá cơ bản: 50k VND / giờ
    
    # Loại bàn: VIP, STANDARD (Thường)
    table_tier = Column(String(50), default="STANDARD")
    
    # Thể loại chơi: LIP (Bida Líp), 3C (Bida Phăng/3 Băng), POOL (Bida Lỗ)
    table_type = Column(String(50), default="LIP")

class PlaySession(Base):
    __tablename__ = "play_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("billiard_tables.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_minutes = Column(Integer, default=0)
    play_fee = Column(Float, default=0.0)
    status = Column(String(50), default="ACTIVE") # ACTIVE, COMPLETED
    
    # Quan he den danh sach mon goi
    order_items = relationship("SessionOrderItem", back_populates="session", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    price = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    category = Column(String(50))
    image_url = Column(String(255), default="")
    
    order_items = relationship("SessionOrderItem", back_populates="product")

class SessionOrderItem(Base):
    __tablename__ = "session_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("play_sessions.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    item_name = Column(String(100))
    quantity = Column(Integer, default=1)
    price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("PlaySession", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

class AIEvent(Base):
    __tablename__ = "ai_events"
    
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("billiard_tables.id"))
    event_type = Column(String(100)) # TABLE_ACTIVE, TABLE_EMPTY, HAND_RAISED
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class StaffNotification(Base):
    __tablename__ = "staff_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("billiard_tables.id"))
    notification_type = Column(String(100))
    status = Column(String(50), default=NotificationStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
