import os
import time
import json
import logging
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger("keycloak_admin")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "bida-realm")

# Service Account credentials for Keycloak Admin API
KEYCLOAK_ADMIN_CLIENT_ID = os.getenv("KEYCLOAK_ADMIN_CLIENT_ID", "bida-app-admin-svc")
KEYCLOAK_ADMIN_CLIENT_SECRET = os.getenv("KEYCLOAK_ADMIN_CLIENT_SECRET", "")

# Fallback master admin credentials (used when service account is not yet generated or during bootstrapping)
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "123456")

# In-memory token cache: {"token": str, "expires_at": float}
_admin_token_cache: Dict[str, Any] = {"token": None, "expires_at": 0}

def get_keycloak_admin_token(force_refresh: bool = False) -> str:
    """
    Lấy access token để gọi Keycloak Admin REST API.
    Có cơ chế in-memory cache và tự động refresh trước khi hết hạn 30 giây.
    """
    now = time.time()
    if not force_refresh and _admin_token_cache["token"] and _admin_token_cache["expires_at"] > now + 30:
        return _admin_token_cache["token"]
    
    # 1. Thử lấy token qua Service Account (client_credentials) nếu có client_secret
    if KEYCLOAK_ADMIN_CLIENT_SECRET:
        token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": KEYCLOAK_ADMIN_CLIENT_ID,
            "client_secret": KEYCLOAK_ADMIN_CLIENT_SECRET
        }
        try:
            resp = requests.post(token_url, data=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                _admin_token_cache["token"] = data["access_token"]
                _admin_token_cache["expires_at"] = now + data.get("expires_in", 300)
                return _admin_token_cache["token"]
        except Exception as e:
            logger.warning(f"Không thể lấy token qua Service Account: {e}. Thử fallback qua master admin.")

    # 2. Fallback qua Master Admin CLI
    master_token_url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    master_payload = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": KEYCLOAK_ADMIN_USER,
        "password": KEYCLOAK_ADMIN_PASSWORD
    }
    resp = requests.post(master_token_url, data=master_payload, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Không thể xác thực Keycloak Admin API ({resp.status_code}): {resp.text}")
    
    data = resp.json()
    _admin_token_cache["token"] = data["access_token"]
    _admin_token_cache["expires_at"] = now + data.get("expires_in", 300)
    return _admin_token_cache["token"]


def get_client_uuid(client_id_name: str = "bida-app") -> str:
    """Lấy internal UUID của Client trong Keycloak dựa theo Client ID name"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients"
    
    resp = requests.get(url, headers=headers, params={"clientId": client_id_name}, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy thông tin Client '{client_id_name}' ({resp.status_code}): {resp.text}")
    
    clients = resp.json()
    if not clients:
        raise ValueError(f"Không tìm thấy Client '{client_id_name}' trong Realm '{KEYCLOAK_REALM}'")
    return clients[0]["id"]


def create_realm_role(role_name: str, description: str = "") -> dict:
    """Tạo mới một Realm Role trong Realm"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles"
    
    body = {
        "name": role_name,
        "description": description
    }
    resp = requests.post(url, headers=headers, json=body, timeout=5)
    if resp.status_code not in (201, 204):
        raise RuntimeError(f"Không thể tạo Realm Role '{role_name}' ({resp.status_code}): {resp.text}")
    
    return get_realm_role(role_name) or body


def get_realm_role(role_name: str) -> Optional[dict]:
    """Lấy thông tin một Realm Role theo tên"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles/{role_name}"
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy thông tin Realm Role '{role_name}' ({resp.status_code}): {resp.text}")
    return resp.json()


def get_realm_roles() -> List[dict]:
    """Lấy toàn bộ danh sách Realm Roles"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles"
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy danh sách Realm Roles ({resp.status_code}): {resp.text}")
    return resp.json()


def get_realm_role_users(role_name: str) -> List[dict]:
    """Lấy danh sách user đang được gán Realm Role role_name"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles/{role_name}/users"
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy danh sách user của Realm Role '{role_name}' ({resp.status_code}): {resp.text}")
    return resp.json()


def delete_realm_role(role_name: str):
    """Xóa một Realm Role khỏi Keycloak"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/roles/{role_name}"
    
    resp = requests.delete(url, headers=headers, timeout=5)
    if resp.status_code not in (200, 204, 404):
        raise RuntimeError(f"Lỗi xóa Realm Role '{role_name}' ({resp.status_code}): {resp.text}")


def create_client_role(client_uuid: str, role_name: str, description: str = "") -> dict:
    """Tạo mới một Client Role trong Client chỉ định"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles"
    
    body = {
        "name": role_name,
        "description": description,
        "clientRole": True
    }
    resp = requests.post(url, headers=headers, json=body, timeout=5)
    if resp.status_code not in (201, 204):
        raise RuntimeError(f"Không thể tạo Client Role '{role_name}' ({resp.status_code}): {resp.text}")
    
    return get_client_role(client_uuid, role_name) or body


def get_client_role(client_uuid: str, role_name: str) -> Optional[dict]:
    """Lấy thông tin chi tiết một Client Role theo tên"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}"
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy thông tin Client Role '{role_name}' ({resp.status_code}): {resp.text}")
    return resp.json()


def get_client_roles(client_uuid: str) -> List[dict]:
    """Lấy toàn bộ danh sách Client Roles của Client"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles"
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy danh sách Client Roles ({resp.status_code}): {resp.text}")
    return resp.json()


def add_composite_roles(client_uuid: str, role_name: str, composite_role_representations: List[dict]):
    """Gán danh sách các role con (permissions) làm Composite Roles cho role_name"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}/composites"
    
    resp = requests.post(url, headers=headers, json=composite_role_representations, timeout=5)
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Lỗi gán Composite Roles cho '{role_name}' ({resp.status_code}): {resp.text}")


def get_role_composites(client_uuid: str, role_name: str) -> List[dict]:
    """Lấy danh sách các permissions (composite roles) của một role"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}/composites"
    
    resp = requests.get(url, headers=headers, timeout=5)
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi lấy composite roles của '{role_name}' ({resp.status_code}): {resp.text}")
    return resp.json()


def delete_client_role(client_uuid: str, role_name: str):
    """Xóa một Client Role khỏi Keycloak"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}"
    
    resp = requests.delete(url, headers=headers, timeout=5)
    if resp.status_code not in (200, 204, 404):
        raise RuntimeError(f"Lỗi xóa Client Role '{role_name}' ({resp.status_code}): {resp.text}")


def add_client_roles_to_user(user_id: str, client_uuid: str, role_representations: List[dict]):
    """Gán Client Roles cho user"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"
    
    resp = requests.post(url, headers=headers, json=role_representations, timeout=5)
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Lỗi gán Client Roles cho user '{user_id}' ({resp.status_code}): {resp.text}")


def create_custom_composite_role(
    role_name: str,
    display_name: str,
    permissions: List[str],
    client_name: str = "bida-app"
) -> dict:
    """
    Tạo Custom Role và gán các permissions làm Composite Roles.
    Có cơ chế ROLLBACK tự động xóa role nếu việc gán composite permissions thất bại.
    """
    client_uuid = get_client_uuid(client_name)
    
    # 1. Kiểm tra xem role đã tồn tại chưa
    existing_role = get_client_role(client_uuid, role_name)
    if existing_role:
        raise ValueError(f"Role '{role_name}' đã tồn tại trong hệ thống")

    # 2. Tìm representation của các permission con
    permission_reps = []
    for perm in permissions:
        perm_rep = get_client_role(client_uuid, perm)
        if not perm_rep:
            raise ValueError(f"Permission '{perm}' chưa được khởi tạo trong Keycloak Client '{client_name}'")
        permission_reps.append(perm_rep)

    # 3. Tạo role cha
    role_created = False
    try:
        create_client_role(client_uuid, role_name, description=display_name)
        role_created = True
        
        # 4. Gán composite permissions
        if permission_reps:
            add_composite_roles(client_uuid, role_name, permission_reps)
            
        return {
            "role_name": role_name,
            "display_name": display_name,
            "permissions": permissions
        }
    except Exception as e:
        # 5. ROLLBACK: Nếu tạo role thành công nhưng gán composite lỗi -> Xóa role cha vừa tạo
        if role_created:
            try:
                delete_client_role(client_uuid, role_name)
            except Exception as rollback_err:
                logger.error(f"Rollback xóa role '{role_name}' thất bại: {rollback_err}")
        raise RuntimeError(f"Lỗi trong quá trình tạo Custom Role và gán permissions: {str(e)}")


def logout_keycloak_user(user_id: str) -> bool:
    """Hủy toàn bộ phiên làm việc (Revoke Sessions) của User trên Keycloak Server"""
    token = get_keycloak_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/logout"
    try:
        resp = requests.post(url, headers=headers, timeout=5)
        return resp.status_code in (200, 204)
    except Exception as e:
        logger.warning(f"Không thể logout Keycloak user {user_id}: {e}")
        return False

