import pytest
import time
from datetime import timedelta
import jwt
from fastapi import HTTPException

class TestJWTAuthTDD:
    def test_create_and_verify_access_token(self):
        """Test tạo và xác thực token JWT hợp lệ với đầy đủ payload."""
        from api.auth import create_access_token, verify_token
        
        payload = {"user_id": 10, "store_id": 1, "role": "STORE_MANAGER"}
        token = create_access_token(payload, expires_delta=timedelta(hours=1))
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        decoded = verify_token(token)
        assert decoded["user_id"] == 10
        assert decoded["store_id"] == 1
        assert decoded["role"] == "STORE_MANAGER"
        assert "exp" in decoded

    def test_expired_token_raises_exception(self):
        """Test token hết hạn phải bị từ chối khi xác thực."""
        from api.auth import create_access_token, verify_token
        
        payload = {"user_id": 10, "store_id": 1, "role": "STORE_MANAGER"}
        # Tạo token đã hết hạn 1 giây trước
        token = create_access_token(payload, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises((jwt.ExpiredSignatureError, HTTPException)) as exc_info:
            verify_token(token)
        if isinstance(exc_info.value, HTTPException):
            assert exc_info.value.status_code == 401

    def test_invalid_signature_raises_exception(self):
        """Test token bị sửa đổi hoặc ký sai chữ ký phải bị từ chối."""
        from api.auth import create_access_token, verify_token
        
        payload = {"user_id": 10, "store_id": 1, "role": "STORE_MANAGER"}
        token = create_access_token(payload, expires_delta=timedelta(hours=1))
        
        # Giả mạo token bằng cách đổi ký tự cuối
        forged_token = token[:-1] + ("a" if token[-1] != "a" else "b")
        
        with pytest.raises((jwt.InvalidTokenError, HTTPException)) as exc_info:
            verify_token(forged_token)
        if isinstance(exc_info.value, HTTPException):
            assert exc_info.value.status_code == 401
