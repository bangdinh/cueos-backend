import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.base import Base

# Import models to ensure they are registered with Base before init_db
from database.models.session import PlaySession, SessionOrderItem
from database.models.customer import CustomerModel
from database.models.notification import StaffNotification
from database.models.store import StoreModel

SQLALCHEMY_DATABASE_URL = "sqlite:///./billing.db"
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
            PlaySession.__table__,
            SessionOrderItem.__table__,
            CustomerModel.__table__,
            StaffNotification.__table__,
            StoreModel.__table__
        ]
    )
