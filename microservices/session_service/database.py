import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.base import Base

from database.models.session import PlaySession
from database.models.billiard_table import BilliardTable
from database.models.notification import AIEvent
from database.models.store import StoreModel

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'session.db')}"
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
            BilliardTable.__table__,
            AIEvent.__table__,
            StoreModel.__table__
        ]
    )
