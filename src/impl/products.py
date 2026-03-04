from app.errors import ApiError
from app.security.rbac import require_roles
from app.security.context import get_current_user

from marketplace_gen.apis.products_api_base import BaseProductsApi
from marketplace_gen.models.product_create import ProductCreate
from marketplace_gen.models.product_update import ProductUpdate
from marketplace_gen.models.product_page_response import ProductPageResponse
from marketplace_gen.models.product_response import ProductResponse


class ProductsApiImpl(BaseProductsApi):
    """
    Реализация CRUD товаров.
    Здесь только:
    - проверка роли
    - вызов product_service
    - возврат DTO
    """

    async def create_product(self, product_create: ProductCreate) -> ProductResponse:
        require_roles("SELLER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO: product_service.create(product_create, user)
        raise ApiError(501, "NOT_IMPLEMENTED", "create_product not implemented", None)

    async def list_products(
        self,
        page: int = 0,
        size: int = 20,
        status=None,
        category=None,
    ) -> ProductPageResponse:
        # Доступно всем авторизованным ролям по матрице (USER/SELLER/ADMIN)
        # TODO: product_service.list(page, size, status, category)
        return ProductPageResponse(items=[], totalElements=0, page=page, size=size)

    async def get_product_by_id(self, id: str) -> ProductResponse:
        # TODO: product_service.get_by_id(id)
        raise ApiError(501, "NOT_IMPLEMENTED", "get_product_by_id not implemented", None)

    async def update_product(self, id: str, product_update: ProductUpdate) -> ProductResponse:
        require_roles("SELLER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO:
        # - если SELLER: проверить, что product.seller_id == user.user_id (лучше в сервисе)
        # - product_service.update(id, product_update, user)
        raise ApiError(501, "NOT_IMPLEMENTED", "update_product not implemented", None)

    async def archive_product(self, id: str) -> ProductResponse:
        require_roles("SELLER", "ADMIN")

        user = get_current_user()
        if user is None:
            raise ApiError(401, "TOKEN_INVALID", "Unauthorized")

        # TODO:
        # - soft delete: status=ARCHIVED
        # - ownership check для SELLER
        # - product_service.archive(id, user)
        raise ApiError(501, "NOT_IMPLEMENTED", "archive_product not implemented", None)