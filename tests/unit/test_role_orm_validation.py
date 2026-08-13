import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.base import Base
from database.models.user import UserStoreRole, UserModel
from database.models.auth_business import StaffInvitation
from database.models import StoreModel

# Use an in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create required seed data for FK constraints
    user = UserModel(id=1, username="testuser", password_hash="hash")
    store = StoreModel(id=1, name="Test Store")
    db.add(user)
    db.add(store)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_user_store_role_valid(db_session):
    role = UserStoreRole(user_id=1, store_id=1, role="OWNER")
    db_session.add(role)
    db_session.commit()
    assert role.id is not None

def test_user_store_role_invalid_raises_error():
    with pytest.raises(ValueError, match="Invalid role"):
        UserStoreRole(user_id=1, store_id=1, role="INVALID_ROLE")

def test_staff_invitation_valid(db_session):
    from datetime import datetime, timedelta
    inv = StaffInvitation(
        store_id=1, 
        phone="0987654321", 
        role="MANAGER", 
        token="abcd", 
        invited_by=1,
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(inv)
    db_session.commit()
    assert inv.id is not None

def test_staff_invitation_invalid_raises_error():
    from datetime import datetime, timedelta
    with pytest.raises(ValueError, match="Invalid role"):
        StaffInvitation(
            store_id=1, 
            phone="0987654321", 
            role="SUPER_ADMIN", # SUPER_ADMIN cannot be invited to a store
            token="abcd", 
            invited_by=1,
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
