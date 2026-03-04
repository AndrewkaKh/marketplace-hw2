from app.errors import ApiError
from app.security.rbac import require_roles

from marketplace_gen.apis.promo_codes_api_base import BasePromoCodesApi
from marketplace_gen.models.promo_code_create import PromoCodeCreate
from marketplace_gen.models.promo_code_response import PromoCodeResponse


class PromoCodesApiImpl(BasePromoCodesApi):
    """
    Реализация /promo-codes.
    В ТЗ: SELLER и ADMIN могут создавать промокоды.
    """

    async def create_promo_code(self, promo_code_create: PromoCodeCreate) -> PromoCodeResponse:
        require_roles("SELLER", "ADMIN")

        # TODO: promo_service.create(promo_code_create)
        raise ApiError(501, "NOT_IMPLEMENTED", "create_promo_code not implemented", None)