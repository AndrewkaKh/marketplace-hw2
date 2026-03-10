from fastapi import APIRouter, Depends, Query, status

from app.security.rbac import require_roles
from app.db.session import db_session
from app.security.context import get_current_user
from app.security.dependencies import get_current_auth
from app.services.product_service import ProductService
from marketplace_gen.models.product_create import ProductCreate
from marketplace_gen.models.product_page_response import ProductPageResponse
from marketplace_gen.models.product_response import ProductResponse
from marketplace_gen.models.product_status import ProductStatus
from marketplace_gen.models.product_update import ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPageResponse, status_code=status.HTTP_200_OK)
async def list_products(
    page: int = Query(default=0, ge=0),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: ProductStatus | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
) -> ProductPageResponse:
    db = next(db_session())
    try:
        return ProductService(db).list(
            page=page,
            size=size,
            status=status_filter.value if status_filter else None,
            category=category,
        )
    finally:
        db.close()


@router.get("/{id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def get_product_by_id(id: int) -> ProductResponse:
    db = next(db_session())
    try:
        return ProductService(db).get_by_id(str(id))
    finally:
        db.close()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    _=Depends(require_roles("SELLER", "ADMIN")),
) -> ProductResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return ProductService(db).create(payload, user)
    finally:
        db.close()


@router.put("/{id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def update_product(
    id: int,
    payload: ProductUpdate,
    _=Depends(require_roles("SELLER", "ADMIN")),
) -> ProductResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return ProductService(db).update(str(id), payload, user)
    finally:
        db.close()


@router.delete("/{id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def archive_product(
    id: int,
    _=Depends(require_roles("SELLER", "ADMIN")),
) -> ProductResponse:
    user = get_current_user()
    db = next(db_session())
    try:
        return ProductService(db).archive(str(id), user)
    finally:
        db.close()