from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from jose import JWTError, jwt

from app.errors import ApiError
from app.security.context import UserContext, current_user
from app.settings import settings

http_bearer = HTTPBearer(auto_error=False)


def create_access_token(*, user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.refresh_token_days)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Access token invalid") from e


async def bearer_auth_dependency(
    security_scopes: SecurityScopes,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
):
    """
    Dependency override для сгенерённого get_token_*.
    Кладёт current_user в contextvar, чтобы impl-слой мог читать пользователя без Request параметра.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Missing bearer token")

    payload = decode_token(credentials.credentials)

    token_type = payload.get("type")
    if token_type != "access":
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Invalid access token type")

    user_id = str(payload.get("sub", ""))
    role = str(payload.get("role", ""))

    if not user_id or role not in {"USER", "SELLER", "ADMIN"}:
        raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Invalid token claims")

    token = current_user.set(UserContext(user_id=user_id, role=role))
    try:
        from marketplace_gen.models.extra_models import TokenModel  # type: ignore

        yield TokenModel(sub=user_id)
    finally:
        current_user.reset(token)
