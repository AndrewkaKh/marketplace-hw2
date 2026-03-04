from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.product import Product, ProductStatus
from app.errors import ApiError
from app.security.context import UserContext
from marketplace_gen.models.product_create import ProductCreate
from marketplace_gen.models.product_page_response import ProductPageResponse
from marketplace_gen.models.product_response import ProductResponse
from marketplace_gen.models.product_update import ProductUpdate


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_response(product: Product) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=float(product.price),
            stock=product.stock,
            category=product.category,
            status=product.status.value if hasattr(product.status, "value") else str(product.status),
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat(),
        )

    def create(self, payload: ProductCreate, user: UserContext) -> ProductResponse:
        seller_id = int(user.user_id) if user.role == "SELLER" else None

        product = Product(
            name=payload.name,
            description=payload.description,
            price=payload.price,
            stock=payload.stock,
            category=payload.category,
            status=ProductStatus(payload.status),
            seller_id=seller_id,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)

    def get_by_id(self, product_id: str) -> ProductResponse:
        product = self.db.get(Product, int(product_id))
        if not product:
            raise ApiError(status_code=404, error_code="PRODUCT_NOT_FOUND", message="Product not found")
        return self._to_response(product)

    def list(self, page: int = 0, size: int = 20, status=None, category=None) -> ProductPageResponse:
        query = select(Product)
        count_query = select(func.count(Product.id))

        if status:
            query = query.where(Product.status == ProductStatus(status))
            count_query = count_query.where(Product.status == ProductStatus(status))

        if category:
            query = query.where(Product.category == category)
            count_query = count_query.where(Product.category == category)

        total = self.db.scalar(count_query) or 0
        items = self.db.scalars(query.offset(page * size).limit(size)).all()

        return ProductPageResponse(
            items=[self._to_response(item) for item in items],
            totalElements=total,
            page=page,
            size=size,
        )

    def update(self, product_id: str, payload: ProductUpdate, user: UserContext) -> ProductResponse:
        product = self.db.get(Product, int(product_id))
        if not product:
            raise ApiError(status_code=404, error_code="PRODUCT_NOT_FOUND", message="Product not found")

        if user.role == "SELLER" and product.seller_id != int(user.user_id):
            raise ApiError(status_code=403, error_code="ACCESS_DENIED", message="Access denied")

        product.name = payload.name
        product.description = payload.description
        product.price = payload.price
        product.stock = payload.stock
        product.category = payload.category
        product.status = ProductStatus(payload.status)

        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)

    def archive(self, product_id: str, user: UserContext) -> ProductResponse:
        product = self.db.get(Product, int(product_id))
        if not product:
            raise ApiError(status_code=404, error_code="PRODUCT_NOT_FOUND", message="Product not found")

        if user.role == "SELLER" and product.seller_id != int(user.user_id):
            raise ApiError(status_code=403, error_code="ACCESS_DENIED", message="Access denied")

        product.status = ProductStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)