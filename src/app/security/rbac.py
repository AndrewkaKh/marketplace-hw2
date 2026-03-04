from app.errors import ApiError
from app.security.context import get_current_user


def require_roles(*roles: str) -> None:
    user = get_current_user()
    if user is None:
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Unauthorized")

    if user.role not in set(roles):
        raise ApiError(status_code=403, error_code="ACCESS_DENIED", message="Access denied")