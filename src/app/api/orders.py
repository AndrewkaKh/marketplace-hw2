from fastapi import APIRouter, Depends, status

from app.security.rbac import require_roles
from app.db.session import db_session
from app.security.context import get_current_user
from app.security.dependencies import get_current_auth
from app.services.order_service import OrderService
from marketplace_gen.models.order_create_request import OrderCreateRequest
from marketplace_gen.models.order_response import OrderResponse
from marketplace_gen.models.order_update_request import OrderUpdateRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    _=Depends(require_roles("USER", "ADMIN")),
) -> OrderResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return OrderService(db).create(int(user.user_id), payload)
    finally:
        db.close()


@router.get("/{id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def get_order_by_id(
    id: int,
    _=Depends(require_roles("USER", "ADMIN")),
) -> OrderResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return OrderService(db).get(int(user.user_id), user.role, str(id))
    finally:
        db.close()


@router.put("/{id}", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def update_order(
    id: int,
    payload: OrderUpdateRequest,
    _=Depends(require_roles("USER", "ADMIN")),
) -> OrderResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return OrderService(db).update(int(user.user_id), user.role, str(id), payload)
    finally:
        db.close()


@router.post("/{id}/cancel", response_model=OrderResponse, status_code=status.HTTP_200_OK)
async def cancel_order(
    id: int,
    _=Depends(require_roles("USER", "ADMIN")),
) -> OrderResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return OrderService(db).cancel(int(user.user_id), user.role, str(id))
    finally:
        db.close()