import pytest
from fastapi.testclient import TestClient
from main import app
from main import app
from database.database import get_db
from database.models import UserModel
from fastapi.testclient import TestClient

class TestBruteForceLogin:
    def test_brute_force_lockout(self):
        """Test user gets locked out after 5 failed login attempts"""
        # Get DB from conftest override
        db = next(get_db())
        user = db.query(UserModel).filter(UserModel.username == "manager1").first()
        # Ensure user exists (conftest handles seeding)
        if not user:
            from database.seed import seed_default_store_and_users
            seed_default_store_and_users(db)
            user = db.query(UserModel).filter(UserModel.username == "manager1").first()
            
        assert user is not None
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        
        with TestClient(app) as client:
            # 1. 4 failed attempts -> still 401 Unauthorized, not locked
            for _ in range(4):
                response = client.post(
                    "/api/auth/login",
                    json={"username": "manager1", "password": "wrong_password"}
                )
                assert response.status_code == 401
                assert "Invalid username or password" in response.json()["detail"]
                
            # Check DB state
        db.refresh(user)
        assert user.failed_login_attempts == 4
        assert user.locked_until is None
        
        with TestClient(app) as client:
            # 2. 5th failed attempt -> locked out
            response = client.post(
                "/api/auth/login",
                json={"username": "manager1", "password": "wrong_password"}
            )
            assert response.status_code == 401 # the 5th attempt itself returns 401 usually, but locks the account
        
        db.refresh(user)
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        
        with TestClient(app) as client:
            # 3. 6th attempt (even with correct pass) -> 403 Forbidden
            response = client.post(
                "/api/auth/login",
                json={"username": "manager1", "password": "secret"}
            )
            assert response.status_code == 403
            assert "Account is temporarily locked" in response.json()["detail"]
        
        # 4. Cleanup
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    def test_successful_login_resets_attempts(self):
        """Test successful login resets failed_login_attempts to 0"""
        db = next(get_db())
        user = db.query(UserModel).filter(UserModel.username == "manager1").first()
        user.failed_login_attempts = 3
        user.locked_until = None
        db.commit()
        
        with TestClient(app) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "manager1", "password": "secret"}
            )
            assert response.status_code == 200
        
        db.refresh(user)
        assert user.failed_login_attempts == 0
