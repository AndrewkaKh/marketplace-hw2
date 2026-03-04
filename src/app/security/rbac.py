from fastapi import Depends

from app.errors import ApiError
from app.security.context import get_current_user
from app.security.dependencies import get_current_auth


def require_roles(*allowed_roles: str):
    async def _checker(_: dict = Depends(get_current_auth)):
        user = get_current_user()
        if user.role not in allowed_roles:
            raise ApiError(status_code=403, error_code="ACCESS_DENIED", message="Access denied")
        return user

    return _checker