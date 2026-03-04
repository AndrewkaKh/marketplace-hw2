from app.db.session import db_session
from app.security.rbac import require_roles
from app.services.promo_service import PromoService
from generated.src.marketplace_gen.models.promo_code_create import PromoCodeCreate
from generated.src.marketplace_gen.models.promo_code_response import PromoCodeResponse
from generated.src.marketplace_gen.apis.promo_codes_api_base import BasePromoCodesApi


class PromoCodesApiImpl(BasePromoCodesApi):
    async def create_promo_code(self, promo_code_create: PromoCodeCreate) -> PromoCodeResponse:
        require_roles("SELLER", "ADMIN")
        db = next(db_session())
        try:
            return PromoService(db).create(promo_code_create)
        finally:
            db.close()