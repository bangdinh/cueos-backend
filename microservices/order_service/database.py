import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.base import Base

# Import models to ensure they are registered with Base
from .models.session import PlaySession, SessionOrderItem
from .models.billiard_table import BilliardTable
from .models.product import Product

SQLALCHEMY_DATABASE_URL = "sqlite:///../../bida_ai.db"
connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
