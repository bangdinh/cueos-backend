from typing import List, Optional
from .value_objects import Money, PlayDuration
from .entities import OrderItem, Table
from domain.store.exceptions import CrossStoreAccessError

class BillAggregate:
    """
    DDD Aggregate Root: Quản lý toàn bộ phiên tính tiền của một bàn bida.
    Nó là đối tượng duy nhất mà bên ngoài (API, Service, UI) được phép giao tiếp để tính toán hóa đơn.
    Đảm bảo tính nhất quán và thực thi các luật nghiệp vụ (VIP surcharge, Discount, Multi-Store Tenant Isolation).
    """
    def __init__(self, table_id: int, table_tier: str, base_hourly_rate: Money, store_id: int = 1):
        self.table_id = table_id
        self.table_tier = table_tier.upper()
        self.base_hourly_rate = base_hourly_rate
        self.store_id = store_id
        self.duration = PlayDuration(0)
        self._items: List[OrderItem] = []
        self._discount_percent: float = 0.0
        self._table: Optional[Table] = None
        
    def assign_table(self, table: Table):
        """Gán bàn chơi và tự validation đảm bảo không thao tác lệch store_id."""
        if table.store_id != self.store_id:
            raise CrossStoreAccessError(
                target_store_id=table.store_id,
                user_store_id=self.store_id,
                message=f"Bàn thuộc cửa hàng {table.store_id} không khớp với hóa đơn cửa hàng {self.store_id}"
            )
        self._table = table
        self.table_id = table.table_id
        self.table_tier = table.table_tier.upper()
        self.base_hourly_rate = table.base_hourly_rate
        
    def set_play_duration(self, duration: PlayDuration):
        self.duration = duration
        
    def add_order_item(self, item: OrderItem):
        """Thêm món và tự validation đảm bảo không thao tác lệch store_id."""
        if item.store_id != self.store_id:
            raise CrossStoreAccessError(
                target_store_id=item.store_id,
                user_store_id=self.store_id,
                message=f"Món gọi thuộc cửa hàng {item.store_id} không khớp với hóa đơn cửa hàng {self.store_id}"
            )
        # Kiểm tra xem món đã có trong bill chưa, nếu có thì cộng dồn số lượng
        for existing in self._items:
            if existing.item_id == item.item_id:
                existing.add_quantity(item.quantity)
                return
        self._items.append(item)
        
    def apply_member_discount(self, percentage: float):
        if not (0.0 <= percentage <= 100.0):
            raise ValueError("Phần trăm giảm giá phải từ 0 đến 100")
        self._discount_percent = percentage
        
    def play_fee(self) -> Money:
        """
        Luật nghiệp vụ:
        - Bàn VIP phụ thu 20% trên giá cơ bản.
        - Tiền giờ = Giá giờ thực tế * Số giờ chơi (tính dựa trên billable_minutes).
        """
        hourly_rate = self.base_hourly_rate
        if self.table_tier == "VIP":
            hourly_rate = hourly_rate * 1.2  # Phụ thu 20%
            
        fee_amount = hourly_rate.amount * self.duration.hours
        return Money(amount=round(fee_amount, 2), currency=self.base_hourly_rate.currency)
        
    def services_fee(self) -> Money:
        """Tổng tiền các món ăn/thức uống."""
        total = Money(0.0, currency=self.base_hourly_rate.currency)
        for item in self._items:
            total = total + item.total_price()
        return total
        
    def calculate_total(self) -> Money:
        """
        Tính tổng hóa đơn sau cùng:
        (Tiền giờ + Tiền dịch vụ) - Giảm giá thành viên.
        """
        subtotal = self.play_fee() + self.services_fee()
        if self._discount_percent > 0:
            discount_amount = subtotal.percentage(self._discount_percent)
            final_amount = subtotal.amount - discount_amount.amount
            return Money(amount=round(final_amount, 2), currency=subtotal.currency)
        return subtotal
