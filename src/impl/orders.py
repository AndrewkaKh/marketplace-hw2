from app.errors import ApiError
from app.security.rbac import require_roles
from app.security.context import get_current_user

from marketplace_gen.apis.orders_api_base import BaseOrdersApi
from marketplace_gen.models.order_create_request import OrderCreateRequest
from marketplace_gen.models.order_update_request import OrderUpdateRequest
from marketplace_gen.models.order_response import OrderResponse


class OrdersApiImpl(BaseOrdersApi):
    """
    Реализация заказов по ТЗ (create/update/get/cancel).
    В impl:
    - роль USER/ADMIN
    - для USER: ownership
    - остальная логика — в order_service (транзакции, stock, promo, user_operations)
    """

    async def create_order(self, order_create_request: OrderCreateRequest) -> OrderResponse:
        require_roles("USER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO: order_service.create(user.user_id, order_create_request)
        raise ApiError(501, "NOT_IMPLEMENTED", "create_order not implemented", None)

    async def get_order_by_id(self, id: str) -> OrderResponse:
        require_roles("USER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO:
        # order = order_service.get(id)
        # if user.role == "USER" and order.user_id != user.user_id -> ORDER_OWNERSHIP_VIOLATION
        raise ApiError(501, "NOT_IMPLEMENTED", "get_order_by_id not implemented", None)

    async def update_order(self, id: str, order_update_request: OrderUpdateRequest) -> OrderResponse:
        require_roles("USER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO: order_service.update(user, id, order_update_request)
        # сервис внутри сделает:
        # - ownership
        # - status == CREATED
        # - UPDATE_ORDER rate limit
        # - return stock
        # - reserve new
        # - promo recalculation
        # - transaction
        raise ApiError(501, "NOT_IMPLEMENTED", "update_order not implemented", None)

    async def cancel_order(self, id: str) -> OrderResponse:
        require_roles("USER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO: order_service.cancel(user, id)
        raise ApiError(501, "NOT_IMPLEMENTED", "cancel_order not implemented", None)