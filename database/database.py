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
db_host = os.getenv("DB_HOST", "127.0.0.1")
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

# Cau hinh connection pool de tranh bi treo/cham khi co nhieu request dong thoi
# pool_pre_ping=True: tu dong kiem tra ket noi truoc khi dung, tranh "stale connection"
# pool_recycle=1800: tai tao ket noi sau 30 phut, tranh bi MySQL server dong ket noi
_pool_kwargs = {}
if "sqlite" not in SQLALCHEMY_DATABASE_URL:
    _pool_kwargs = {
        "pool_size": 10,       # So ket noi toi da trong pool
        "max_overflow": 20,    # So ket noi them co the tao khi pool day
        "pool_timeout": 10,    # Cho toi da 10s de lay ket noi tu pool
        "pool_recycle": 1800,  # Tai tao ket noi sau 30 phut
        "pool_pre_ping": True, # Kiem tra ket noi truoc khi su dung
    }

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, **_pool_kwargs)
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
            alter_stmts = [
                "ALTER TABLE products ADD COLUMN image_url VARCHAR(255) DEFAULT ''",
                "ALTER TABLE products ADD COLUMN store_id INT NOT NULL DEFAULT 1",
                "ALTER TABLE billiard_tables ADD COLUMN store_id INT NOT NULL DEFAULT 1",
                "ALTER TABLE play_sessions ADD COLUMN store_id INT NOT NULL DEFAULT 1",
                "ALTER TABLE play_sessions ADD COLUMN is_synced_to_hq BOOLEAN DEFAULT 0",
                "ALTER TABLE play_sessions ADD COLUMN services_fee FLOAT DEFAULT 0.0",
                "ALTER TABLE play_sessions ADD COLUMN total_amount FLOAT DEFAULT 0.0",
                "ALTER TABLE session_order_items ADD COLUMN store_id INT NOT NULL DEFAULT 1",
                "ALTER TABLE ai_events ADD COLUMN store_id INT NOT NULL DEFAULT 1",
                "ALTER TABLE staff_notifications ADD COLUMN store_id INT NOT NULL DEFAULT 1"
            ]
            for stmt in alter_stmts:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass
    except Exception:
        pass
