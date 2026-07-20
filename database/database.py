import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

# Lay duong dan den thu muc goc cua du an de load .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
db_user = os.getenv("DB_USER", "postgres")
db_pass = os.getenv("DB_PASSWORD", "")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "bida_db")

SQLALCHEMY_DATABASE_URL = "sqlite:///./bida_ai.db"
connect_args = {"check_same_thread": False}

if db_type == "postgresql":
    pg_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    try:
        # Thu ket noi PostgreSQL voi timeout la 3 giay
        temp_engine = create_engine(pg_url, connect_args={"connect_timeout": 3})
        with temp_engine.connect() as conn:
            pass
        # Neu ket noi thanh cong, su dung PG URL
        SQLALCHEMY_DATABASE_URL = pg_url
        connect_args = {}
        print(f"[DB] Ket noi thanh cong Postgres o {db_host}:{db_port}")
    except Exception as e:
        print(f"[DB WARNING] Khong the ket noi PostgreSQL: {e}")
        print("[DB WARNING] Tu dong quay ve dung database SQLite de tranh loi sap ung dung.")
        SQLALCHEMY_DATABASE_URL = "sqlite:///./bida_ai.db"
        connect_args = {"check_same_thread": False}
elif db_type == "mysql":
    mysql_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    try:
        # Thu ket noi MySQL voi timeout la 3 giay
        temp_engine = create_engine(mysql_url, connect_args={"connect_timeout": 3})
        with temp_engine.connect() as conn:
            pass
        SQLALCHEMY_DATABASE_URL = mysql_url
        connect_args = {}
        print(f"[DB] Ket noi thanh cong MySQL o {db_host}:{db_port}")
    except Exception as e:
        print(f"[DB WARNING] Khong the ket noi MySQL: {e}")
        print("[DB WARNING] Tu dong quay ve dung database SQLite de tranh loi sap ung dung.")
        SQLALCHEMY_DATABASE_URL = "sqlite:///./bida_ai.db"
        connect_args = {"check_same_thread": False}
else:
    print("[DB] Su dung database SQLite mac dinh.")

# FIX BUG: Truyen connect_args dung format tu dien
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
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(255) DEFAULT ''"))
    except Exception:
        pass
