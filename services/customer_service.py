import os
import requests
from typing import Optional, List, Dict

CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://127.0.0.1:8007")

class CustomerService:
    """HTTP Client gọi sang customer_service (Port 8007) để quản lý thông tin khách hàng và tích điểm."""
    
    @staticmethod
    def get_customer_by_id(db=None, customer_id: int = 0) -> Optional[Dict]:
        """Lấy thông tin khách hàng bằng ID qua HTTP API."""
        try:
            resp = requests.get(f"{CUSTOMER_SERVICE_URL}/api/customers/{customer_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    @staticmethod
    def get_customer_by_phone(db=None, phone: str = "") -> Optional[Dict]:
        """Lấy thông tin khách hàng bằng số điện thoại qua HTTP API."""
        try:
            resp = requests.get(f"{CUSTOMER_SERVICE_URL}/api/customers", params={"phone": phone}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data[0] if data else None
        except Exception:
            pass
        return None

    @staticmethod
    def get_customers_by_store(db=None, store_id: int = 0) -> List[Dict]:
        """Lấy danh sách khách hàng của một chi nhánh cụ thể qua HTTP API."""
        try:
            resp = requests.get(f"{CUSTOMER_SERVICE_URL}/api/customers", params={"store_id": store_id}, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    @staticmethod
    def create_or_update_customer(db=None, name: str = "", phone: str = "", store_id: Optional[int] = None) -> Optional[Dict]:
        """Tạo mới hoặc cập nhật thông tin khách hàng qua HTTP API."""
        existing = CustomerService.get_customer_by_phone(phone=phone)
        if existing:
            try:
                resp = requests.put(
                    f"{CUSTOMER_SERVICE_URL}/api/customers/{existing['id']}",
                    json={"name": name, "store_id": store_id},
                    timeout=5
                )
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass
            return existing
        else:
            try:
                resp = requests.post(
                    f"{CUSTOMER_SERVICE_URL}/api/customers",
                    json={"name": name, "phone": phone, "store_id": store_id, "points": 0},
                    timeout=5
                )
                if resp.status_code in (200, 201):
                    return resp.json()
            except Exception:
                pass
            return None

    @staticmethod
    def add_points(db=None, customer_id: int = 0, points: int = 0, reason: str = "Tích điểm") -> Optional[Dict]:
        """Tích lũy điểm cho khách hàng qua HTTP API."""
        try:
            resp = requests.put(
                f"{CUSTOMER_SERVICE_URL}/api/customers/{customer_id}/points",
                json={"points_delta": points, "reason": reason},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None
