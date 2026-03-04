from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.promo_code import PromoCode, PromoDiscountType
from app.errors import ApiError
from marketplace_gen.models.promo_code_create import PromoCodeCreate
from marketplace_gen.models.promo_code_response import PromoCodeResponse


class PromoService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_response(promo: PromoCode) -> PromoCodeResponse:
        return PromoCodeResponse(
            id=promo.id,
            code=promo.code,
            discount_type=promo.discount_type.value,
            discount_value=float(promo.discount_value),
            min_order_amount=float(promo.min_order_amount),
            max_uses=promo.max_uses,
            current_uses=promo.current_uses,
            valid_from=promo.valid_from.isoformat(),
            valid_until=promo.valid_until.isoformat(),
            active=promo.active,
            created_at=promo.created_at.isoformat(),
        )

    def create(self, payload: PromoCodeCreate) -> PromoCodeResponse:
        existing = self.db.scalar(select(PromoCode).where(PromoCode.code == payload.code))
        if existing:
            raise ApiError(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Validation failed",
                details={"violations": [{"field": "code", "rule": "unique", "message": "Promo code already exists"}]},
            )

        promo = PromoCode(
            code=payload.code,
            discount_type=PromoDiscountType(payload.discount_type),
            discount_value=payload.discount_value,
            min_order_amount=payload.min_order_amount,
            max_uses=payload.max_uses,
            current_uses=0,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            active=payload.active,
        )
        self.db.add(promo)
        self.db.commit()
        self.db.refresh(promo)
        return self._to_response(promo)