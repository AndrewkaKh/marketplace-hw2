from fastapi import APIRouter, Depends, status

from app.db.session import db_session
from app.security.rbac import require_roles
from app.services.promo_service import PromoService
from marketplace_gen.models.promo_code_create import PromoCodeCreate
from marketplace_gen.models.promo_code_response import PromoCodeResponse

router = APIRouter(prefix="/promo-codes", tags=["promo-codes"])


@router.post("", response_model=PromoCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    payload: PromoCodeCreate,
    _=Depends(require_roles("SELLER", "ADMIN")),
) -> PromoCodeResponse:
    db = next(db_session())
    try:
        return PromoService(db).create(payload)
    finally:
        db.close()