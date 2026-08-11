import pytest
from datetime import datetime, timedelta

# Nhập các class nghiệp vụ (Domain Objects) - Hiện tại chưa có code thực tế (Sẽ fail khi chạy - bước RED)
try:
    from domain.billing.value_objects import Money, PlayDuration
    from domain.billing.entities import OrderItem, Table
    from domain.billing.aggregates import BillAggregate
    from domain.store.exceptions import CrossStoreAccessError
except ImportError:
    pass

class TestBillingDomainTDD:
    """
    TDD Phase 1 (RED): Viết các Unit Test xác định luật nghiệp vụ (Business Rules) của Bida AI.
    """

    def test_money_value_object_immutability_and_addition(self):
        """Test Value Object Money: Bất biến (Immutable) và cộng tiền hợp lệ."""
        m1 = Money(50000)
        m2 = Money(25000)
        total = m1 + m2
        
        assert total.amount == 75000
        assert total.currency == "VND"
        # Đảm bảo tính bất biến (m1 và m2 không bị thay đổi giá trị)
        assert m1.amount == 50000

    def test_play_duration_minimum_rounding(self):
        """Test Value Object PlayDuration: Luật nghiệp vụ dưới 15 phút tính tròn thành 15 phút tối thiểu."""
        duration = PlayDuration(minutes=10)
        assert duration.billable_minutes == 15
        
        duration_normal = PlayDuration(minutes=45)
        assert duration_normal.billable_minutes == 45

    def test_order_item_total_price_calculation(self):
        """Test Entity OrderItem: Tính tổng tiền món ăn/thức uống dựa trên số lượng."""
        item = OrderItem(item_id=1, name="Coca Cola", unit_price=Money(15000), quantity=3)
        assert item.total_price().amount == 45000

    def test_bill_aggregate_calculation_for_standard_table(self):
        """
        Test Aggregate Root BillAggregate:
        - Bàn Thường (STANDARD): Giá 50,000 VND / giờ.
        - Chơi 60 phút => Tiền giờ: 50,000 VND.
        - Gọi 2 Coca (15,000 * 2 = 30,000 VND).
        - Tổng hóa đơn: 80,000 VND.
        """
        bill = BillAggregate(
            table_id=1,
            table_tier="STANDARD",
            base_hourly_rate=Money(50000)
        )
        
        bill.set_play_duration(PlayDuration(60))
        bill.add_order_item(OrderItem(item_id=1, name="Coca Cola", unit_price=Money(15000), quantity=2))
        
        total_invoice = bill.calculate_total()
        assert bill.play_fee().amount == 50000
        assert bill.services_fee().amount == 30000
        assert total_invoice.amount == 80000

    def test_bill_aggregate_vip_table_surcharge_and_discount(self):
        """
        Test Aggregate Root BillAggregate với Bàn VIP và Giảm giá thành viên:
        - Bàn VIP phụ thu 20% tiền giờ (50k * 1.2 = 60,000 VND / giờ).
        - Chơi 60 phút => Tiền giờ: 60,000 VND.
        - Giảm giá thành viên 10% trên tổng hóa đơn.
        - Tổng hóa đơn sau giảm: 60,000 * 0.9 = 54,000 VND.
        """
        bill = BillAggregate(
            table_id=2,
            table_tier="VIP",
            base_hourly_rate=Money(50000)
        )
        
        bill.set_play_duration(PlayDuration(60))
        bill.apply_member_discount(percentage=10.0)
        
        assert bill.play_fee().amount == 60000  # Đã tính phụ thu VIP 20%
        assert bill.calculate_total().amount == 54000  # Đã giảm 10%

    def test_bill_aggregate_store_id_assignment(self):
        """Test BillAggregate nhận store_id và cho phép thêm OrderItem/Table cùng store_id."""
        bill = BillAggregate(
            table_id=10,
            table_tier="STANDARD",
            base_hourly_rate=Money(50000),
            store_id=5
        )
        assert bill.store_id == 5
        
        table = Table(table_id=10, name="Bàn 1", table_tier="STANDARD", base_hourly_rate=Money(50000), store_id=5)
        bill.assign_table(table)
        
        item = OrderItem(item_id=1, name="Coca", unit_price=Money(15000), quantity=1, store_id=5)
        bill.add_order_item(item)
        assert len(bill._items) == 1

    def test_bill_aggregate_cross_store_access_raises_error(self):
        """Test BillAggregate ném CrossStoreAccessError khi thêm OrderItem hoặc Table khác store_id."""
        bill = BillAggregate(
            table_id=10,
            table_tier="STANDARD",
            base_hourly_rate=Money(50000),
            store_id=1
        )
        
        table_other_store = Table(table_id=20, name="Bàn 2 Quán Khác", table_tier="STANDARD", base_hourly_rate=Money(50000), store_id=2)
        with pytest.raises(CrossStoreAccessError) as exc_info:
            bill.assign_table(table_other_store)
        assert "Bàn thuộc cửa hàng 2 không khớp với hóa đơn cửa hàng 1" in str(exc_info.value)
        
        item_other_store = OrderItem(item_id=1, name="Sting", unit_price=Money(15000), quantity=1, store_id=2)
        with pytest.raises(CrossStoreAccessError) as exc_info:
            bill.add_order_item(item_other_store)
        assert "Món gọi thuộc cửa hàng 2 không khớp với hóa đơn cửa hàng 1" in str(exc_info.value)
