import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import get_db
from database.models import UserModel
from database.models.auth_business import AuditLog

class TestAuditLogs:
    def test_audit_log_created_on_lockout(self):
        """Test that an ACCOUNT_LOCKED audit log is created when brute force limit is reached."""
        db = next(get_db())
        user = db.query(UserModel).filter(UserModel.username == "manager1").first()
        if not user:
            from database.seed import seed_default_store_and_users
            seed_default_store_and_users(db)
            user = db.query(UserModel).filter(UserModel.username == "manager1").first()
            
        # Clear previous attempts and logs
        user.failed_login_attempts = 4
        user.locked_until = None
        db.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.action == "ACCOUNT_LOCKED").delete()
        db.commit()

        with TestClient(app) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "manager1", "password": "wrong_password"}
            )
            assert response.status_code == 401
            
            # Now failed attempts should be 5 and locked_until should be set
            db.refresh(user)
            assert user.failed_login_attempts == 5
            assert user.locked_until is not None
            
            # Check AuditLog
            audit = db.query(AuditLog).filter(AuditLog.user_id == user.id, AuditLog.action == "ACCOUNT_LOCKED").first()
            assert audit is not None
            assert audit.target_type == "USER"
            assert audit.target_id == user.id
            assert audit.ip_address is not None  # TestClient injects 127.0.0.1 typically, but we accept string IP

    def test_audit_log_created_on_tokens_revoked(self):
        """Test that a TOKENS_REVOKED audit log is created when super admin revokes tokens."""
        db = next(get_db())
        user = db.query(UserModel).filter(UserModel.username == "manager1").first()
        admin_user = db.query(UserModel).filter(UserModel.username == "admin").first()
        
        db.query(AuditLog).filter(AuditLog.target_id == user.id, AuditLog.action == "TOKENS_REVOKED").delete()
        db.commit()
        
        with TestClient(app) as client:
            # Login as admin to get token
            r_admin = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})
            admin_token = r_admin.json()["access_token"]
            
            # Revoke tokens for manager1
            r_revoke = client.post(
                f"/api/auth/revoke_tokens/{user.id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert r_revoke.status_code == 200
            
            # Check AuditLog
            audit = db.query(AuditLog).filter(AuditLog.target_id == user.id, AuditLog.action == "TOKENS_REVOKED").first()
            assert audit is not None
            assert audit.target_type == "USER"
            assert audit.target_id == user.id
            assert audit.user_id == admin_user.id
