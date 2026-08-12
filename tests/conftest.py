import os
import pytest

# Ensure TESTING is set before any imports that initialize DB
os.environ["TESTING"] = "1"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    from database.database import init_db, SessionLocal, get_db
    from main import app
    init_db()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    app.dependency_overrides.clear()
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
