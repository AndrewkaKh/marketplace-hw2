from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.order import Order, OrderItem, OrderStatus
from app.db.models.product import Product, ProductStatus
from app.db.models.promo_code import PromoCode, PromoDiscountType
from app.db.models.user_operation import UserOperation, UserOperationType
from app.errors import ApiError
from app.settings import settings
from marketplace_gen.models.order_create_request import OrderCreateRequest
from marketplace_gen.models.order_response import OrderResponse
from marketplace_gen.models.order_update_request import OrderUpdateRequest


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_response(order: Order, items: list[OrderItem], promo_code: str | None) -> OrderResponse:
        from marketplace_gen.models.order_item_response import OrderItemResponse

        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status.value,
            promo_code=promo_code,
            total_amount=float(order.total_amount),
            discount_amount=float(order.discount_amount),
            items=[
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_order=float(item.price_at_order),
                )
                for item in items
            ],
            created_at=order.created_at.isoformat(),
            updated_at=order.updated_at.isoformat(),
        )

    def _check_rate_limit(self, user_id: int, op_type: UserOperationType):
        last_op = self.db.scalar(
            select(UserOperation)
            .where(UserOperation.user_id == user_id, UserOperation.operation_type == op_type)
            .order_by(UserOperation.created_at.desc())
            .limit(1)
        )
        if last_op and last_op.created_at > datetime.now(timezone.utc) - timedelta(minutes=settings.order_rate_limit_minutes):
            raise ApiError(status_code=429, error_code="ORDER_LIMIT_EXCEEDED", message="Order rate limit exceeded")

    def _get_active_order(self, user_id: int):
        return self.db.scalar(
            select(Order).where(
                Order.user_id == user_id,
                Order.status.in_([OrderStatus.CREATED, OrderStatus.PAYMENT_PENDING]),
            )
        )

    def _apply_promo(self, promo: PromoCode, total_amount: float) -> tuple[float, float]:
        now = datetime.now(timezone.utc)
        if not promo.active or promo.current_uses >= promo.max_uses or not (promo.valid_from <= now <= promo.valid_until):
            raise ApiError(status_code=422, error_code="PROMO_CODE_INVALID", message="Promo code invalid")

        if total_amount < float(promo.min_order_amount):
            raise ApiError(status_code=422, error_code="PROMO_CODE_MIN_AMOUNT", message="Order amount below promo minimum")

        if promo.discount_type == PromoDiscountType.PERCENTAGE:
            discount = total_amount * float(promo.discount_value) / 100.0
            discount = min(discount, total_amount * 0.7)
        else:
            discount = min(float(promo.discount_value), total_amount)

        return discount, total_amount - discount

    def create(self, user_id: int, payload: OrderCreateRequest) -> OrderResponse:
        self._check_rate_limit(user_id, UserOperationType.CREATE_ORDER)

        if self._get_active_order(user_id):
            raise ApiError(status_code=409, error_code="ORDER_HAS_ACTIVE", message="User already has active order")

        products = []
        insufficient = []

        for item in payload.items:
            product = self.db.get(Product, int(item.product_id))
            if not product:
                raise ApiError(status_code=404, error_code="PRODUCT_NOT_FOUND", message="Product not found")
            if product.status != ProductStatus.ACTIVE:
                raise ApiError(status_code=409, error_code="PRODUCT_INACTIVE", message="Product is inactive")
            if product.stock < item.quantity:
                insufficient.append(
                    {
                        "product_id": product.id,
                        "requested": item.quantity,
                        "available": product.stock,
                    }
                )
            products.append((product, item))

        if insufficient:
            raise ApiError(
                status_code=409,
                error_code="INSUFFICIENT_STOCK",
                message="Insufficient stock",
                details={"items": insufficient},
            )

        total_before_discount = 0.0
        order_items_to_create = []

        for product, item in products:
            product.stock -= item.quantity
            total_before_discount += float(product.price) * item.quantity
            order_items_to_create.append((product, item))

        promo = None
        discount_amount = 0.0
        total_amount = total_before_discount

        if payload.promo_code:
            promo = self.db.scalar(select(PromoCode).where(PromoCode.code == payload.promo_code))
            if not promo:
                raise ApiError(status_code=422, error_code="PROMO_CODE_INVALID", message="Promo code invalid")
            discount_amount, total_amount = self._apply_promo(promo, total_before_discount)
            promo.current_uses += 1

        order = Order(
            user_id=user_id,
            status=OrderStatus.CREATED,
            promo_code_id=promo.id if promo else None,
            total_amount=total_amount,
            discount_amount=discount_amount,
        )
        self.db.add(order)
        self.db.flush()

        created_items = []
        for product, item in order_items_to_create:
            row = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price_at_order=product.price,
            )
            self.db.add(row)
            created_items.append(row)

        self.db.add(UserOperation(user_id=user_id, operation_type=UserOperationType.CREATE_ORDER))
        self.db.commit()
        self.db.refresh(order)

        return self._to_response(order, created_items, promo.code if promo else None)

    def get(self, current_user_id: int, current_role: str, order_id: str) -> OrderResponse:
        order = self.db.get(Order, int(order_id))
        if not order:
            raise ApiError(status_code=404, error_code="ORDER_NOT_FOUND", message="Order not found")

        if current_role == "USER" and order.user_id != current_user_id:
            raise ApiError(
                status_code=403,
                error_code="ORDER_OWNERSHIP_VIOLATION",
                message="Order belongs to another user",
            )

        items = self.db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        promo = self.db.get(PromoCode, order.promo_code_id) if order.promo_code_id else None
        return self._to_response(order, items, promo.code if promo else None)

    def cancel(self, current_user_id: int, current_role: str, order_id: str) -> OrderResponse:
        order = self.db.get(Order, int(order_id))
        if not order:
            raise ApiError(status_code=404, error_code="ORDER_NOT_FOUND", message="Order not found")

        if current_role == "USER" and order.user_id != current_user_id:
            raise ApiError(
                status_code=403,
                error_code="ORDER_OWNERSHIP_VIOLATION",
                message="Order belongs to another user",
            )

        if order.status not in {OrderStatus.CREATED, OrderStatus.PAYMENT_PENDING}:
            raise ApiError(
                status_code=409,
                error_code="INVALID_STATE_TRANSITION",
                message="Cancel not allowed from current state",
            )

        items = self.db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in items:
            product = self.db.get(Product, item.product_id)
            if product:
                product.stock += item.quantity

        promo = self.db.get(PromoCode, order.promo_code_id) if order.promo_code_id else None
        if promo and promo.current_uses > 0:
            promo.current_uses -= 1

        order.status = OrderStatus.CANCELED
        self.db.commit()
        self.db.refresh(order)
        return self._to_response(order, items, promo.code if promo else None)

    def update(self, current_user_id: int, current_role: str, order_id: str, payload: OrderUpdateRequest) -> OrderResponse:
        self._check_rate_limit(current_user_id, UserOperationType.UPDATE_ORDER)

        order = self.db.get(Order, int(order_id))
        if not order:
            raise ApiError(status_code=404, error_code="ORDER_NOT_FOUND", message="Order not found")

        if current_role == "USER" and order.user_id != current_user_id:
            raise ApiError(
                status_code=403,
                error_code="ORDER_OWNERSHIP_VIOLATION",
                message="Order belongs to another user",
            )

        if order.status != OrderStatus.CREATED:
            raise ApiError(
                status_code=409,
                error_code="INVALID_STATE_TRANSITION",
                message="Order update allowed only in CREATED",
            )

        existing_items = self.db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in existing_items:
            product = self.db.get(Product, item.product_id)
            if product:
                product.stock += item.quantity

        for item in existing_items:
            self.db.delete(item)

        products = []
        insufficient = []
        for item in payload.items:
            product = self.db.get(Product, int(item.product_id))
            if not product:
                raise ApiError(status_code=404, error_code="PRODUCT_NOT_FOUND", message="Product not found")
            if product.status != ProductStatus.ACTIVE:
                raise ApiError(status_code=409, error_code="PRODUCT_INACTIVE", message="Product is inactive")
            if product.stock < item.quantity:
                insufficient.append(
                    {
                        "product_id": product.id,
                        "requested": item.quantity,
                        "available": product.stock,
                    }
                )
            products.append((product, item))

        if insufficient:
            raise ApiError(
                status_code=409,
                error_code="INSUFFICIENT_STOCK",
                message="Insufficient stock",
                details={"items": insufficient},
            )

        total_before_discount = 0.0
        created_items = []
        for product, item in products:
            product.stock -= item.quantity
            total_before_discount += float(product.price) * item.quantity
            row = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price_at_order=product.price,
            )
            self.db.add(row)
            created_items.append(row)

        discount_amount = 0.0
        total_amount = total_before_discount
        promo = self.db.get(PromoCode, order.promo_code_id) if order.promo_code_id else None

        if promo:
            if total_before_discount < float(promo.min_order_amount):
                if promo.current_uses > 0:
                    promo.current_uses -= 1
                order.promo_code_id = None
                promo = None
            else:
                discount_amount, total_amount = self._apply_promo(promo, total_before_discount)

        order.discount_amount = discount_amount
        order.total_amount = total_amount

        self.db.add(UserOperation(user_id=current_user_id, operation_type=UserOperationType.UPDATE_ORDER))
        self.db.commit()
        self.db.refresh(order)

        return self._to_response(order, created_items, promo.code if promo else None)