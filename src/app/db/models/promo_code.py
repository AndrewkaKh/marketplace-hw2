import enum
from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromoDiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    discount_type: Mapped[PromoDiscountType] = mapped_column(
        Enum(PromoDiscountType, name="promo_discount_type"), nullable=False
    )
    discount_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    min_order_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False)
    current_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_from: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)