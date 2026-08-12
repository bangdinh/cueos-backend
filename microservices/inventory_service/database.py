import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.base import Base
# Import models to ensure they are registered with Base before init_db
from database.models.product import Product
from database.models.billiard_table import BilliardTable
from database.models.store import StoreModel

SQLALCHEMY_DATABASE_URL = "sqlite:///./inventory.db"
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
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Product.__table__,
            BilliardTable.__table__,
            StoreModel.__table__
        ]
    )
