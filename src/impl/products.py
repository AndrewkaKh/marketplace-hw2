from app.security.rbac import require_roles
from app.db.session import db_session
from app.security.context import get_current_user
from app.services.product_service import ProductService

from generated.src.marketplace_gen.apis.products_api_base import BaseProductsApi
from generated.src.marketplace_gen.models.product_create import ProductCreate
from generated.src.marketplace_gen.models.product_update import ProductUpdate
from generated.src.marketplace_gen.models.product_page_response import ProductPageResponse
from generated.src.marketplace_gen.models.product_response import ProductResponse


class ProductsApiImpl(BaseProductsApi):
    async def create_product(self, product_create: ProductCreate) -> ProductResponse:
        require_roles("SELLER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return ProductService(db).create(product_create, user)
        finally:
            db.close()

    async def list_products(
        self,
        page: int = 0,
        size: int = 20,
        status=None,
        category=None,
    ) -> ProductPageResponse:
        db = next(db_session())
        try:
            return ProductService(db).list(page=page, size=size, status=status, category=category)
        finally:
            db.close()

    async def get_product_by_id(self, id: str) -> ProductResponse:
        db = next(db_session())
        try:
            return ProductService(db).get_by_id(id)
        finally:
            db.close()

    async def update_product(self, id: str, product_update: ProductUpdate) -> ProductResponse:
        require_roles("SELLER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return ProductService(db).update(id, product_update, user)
        finally:
            db.close()

    async def archive_product(self, id: str) -> ProductResponse:
        require_roles("SELLER", "ADMIN")
        user = get_current_user()
        db = next(db_session())
        try:
            return ProductService(db).archive(id, user)
        finally:
            db.close()