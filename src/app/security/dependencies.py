from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import ApiError
from app.security.context import UserContext, current_user
from app.security.jwt import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Invalid access token type")

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or role not in {"USER", "SELLER", "ADMIN"}:
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Invalid token claims")

    token = current_user.set(UserContext(user_id=str(user_id), role=str(role)))
    return payload