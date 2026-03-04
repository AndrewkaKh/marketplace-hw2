from app.db.session import db_session
from app.security.context import get_current_user
from app.security.rbac import require_roles
from app.services.order_service import OrderService
from generated.src.marketplace_gen.apis.orders_api_base import BaseOrdersApi
from generated.src.marketplace_gen.models.order_create_request import OrderCreateRequest
from generated.src.marketplace_gen.models.order_response import OrderResponse
from generated.src.marketplace_gen.models.order_update_request import OrderUpdateRequest


class OrdersApiImpl(BaseOrdersApi):
    async def create_order(self, order_create_request: OrderCreateRequest) -> OrderResponse:
        require_roles("USER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return OrderService(db).create(int(user.user_id), order_create_request)
        finally:
            db.close()

    async def get_order_by_id(self, id: str) -> OrderResponse:
        require_roles("USER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return OrderService(db).get(int(user.user_id), user.role, id)
        finally:
            db.close()

    async def update_order(self, id: str, order_update_request: OrderUpdateRequest) -> OrderResponse:
        require_roles("USER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return OrderService(db).update(int(user.user_id), user.role, id, order_update_request)
        finally:
            db.close()

    async def cancel_order(self, id: str) -> OrderResponse:
        require_roles("USER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return OrderService(db).cancel(int(user.user_id), user.role, id)
        finally:
            db.close()