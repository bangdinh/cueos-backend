import os
from typing import Optional, List, Dict
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
REALM_NAME = os.getenv("KEYCLOAK_REALM", "bida-realm")
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/certs"

jwks_client = PyJWKClient(JWKS_URL)
security = HTTPBearer(auto_error=True)

def get_current_keycloak_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Keycloak đã hết hạn (Expired Token)",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token không hợp lệ hoặc không thể xác thực với Keycloak: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_customer_role(user: Dict = Depends(get_current_keycloak_user)) -> Dict:
    client_roles = user.get("resource_access", {}).get("bida-app", {}).get("roles", [])
    realm_roles = user.get("realm_access", {}).get("roles", [])
    all_roles = client_roles + realm_roles
    
    if "CUSTOMER" not in all_roles and "SUPER_ADMIN" not in all_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền Khách hàng (Yêu cầu role CUSTOMER)"
        )
    return user
