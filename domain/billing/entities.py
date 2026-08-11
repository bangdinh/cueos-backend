from dataclasses import dataclass
from .value_objects import Money

@dataclass
class OrderItem:
    """
    DDD Entity: Món ăn/thức uống hoặc dịch vụ được gọi trong một phiên chơi.
    Có định danh (item_id) và có hành vi tự tính tổng tiền cho chính nó.
    Thêm store_id để đảm bảo cách ly dữ liệu từng cửa hàng.
    """
    item_id: int
    name: str
    unit_price: Money
    quantity: int = 1
    store_id: int = 1
    
    def total_price(self) -> Money:
        """Quy tắc tính giá của món: giá đơn vị * số lượng."""
        return self.unit_price * float(self.quantity)
    
    def add_quantity(self, qty: int):
        if self.quantity + qty < 0:
            raise ValueError("Số lượng không thể âm")
        self.quantity += qty

@dataclass
class Table:
    """
    DDD Entity: Bàn bida.
    """
    table_id: int
    name: str
    table_tier: str
    base_hourly_rate: Money
    store_id: int = 1
