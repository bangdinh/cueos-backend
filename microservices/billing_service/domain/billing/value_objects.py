from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    """
    DDD Value Object: Đại diện cho tiền tệ.
    frozen=True đảm bảo tính bất biến (Immutable) - một khi đã tạo ra thì không thể sửa amount hay currency.
    Mọi thao tác cộng, nhân đều tạo ra một Value Object Money mới.
    """
    amount: float
    currency: str = "VND"
    
    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise ValueError("Chỉ có thể cộng Money với Money")
        if self.currency != other.currency:
            raise ValueError("Không thể cộng hai loại tiền tệ khác nhau")
        return Money(amount=self.amount + other.amount, currency=self.currency)
        
    def __mul__(self, factor: float) -> "Money":
        return Money(amount=round(self.amount * factor, 2), currency=self.currency)

    def percentage(self, percent: float) -> "Money":
        """Tính phần trăm tiền (ví dụ: giảm giá 10% -> percentage(10))."""
        return self * (percent / 100.0)


@dataclass(frozen=True)
class PlayDuration:
    """
    DDD Value Object: Đại diện cho thời gian chơi bida (tính bằng phút).
    Quy tắc nghiệp vụ (Domain Rule):
    - Nếu thời gian chơi dưới 15 phút, tự động làm tròn thành 15 phút (mức tối thiểu của quán).
    """
    minutes: int
    
    @property
    def billable_minutes(self) -> int:
        return max(15, self.minutes)
    
    @property
    def hours(self) -> float:
        return self.billable_minutes / 60.0
