from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict

from app.errors import ApiError
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from marketplace_gen.apis.auth_api_base import BaseAuthApi
from marketplace_gen.models.access_token_response import AccessTokenResponse
from marketplace_gen.models.auth_tokens_response import AuthTokensResponse
from marketplace_gen.models.login_request import LoginRequest
from marketplace_gen.models.refresh_request import RefreshRequest
from marketplace_gen.models.register_request import RegisterRequest
from marketplace_gen.models.user_response import UserResponse

# Простое in-memory хранилище для быстрого старта (НЕ финальное решение)
_USERS_BY_EMAIL: Dict[str, dict] = {}
_REFRESH_TOKENS: Dict[str, str] = {}  # refresh_token -> user_id


class AuthApiImpl(BaseAuthApi):
    async def register(self, register_request: RegisterRequest) -> UserResponse:
        email = register_request.email.lower().strip()

        if email in _USERS_BY_EMAIL:
            # В ТЗ нет отдельного кода "EMAIL_ALREADY_EXISTS", поэтому пока дадим VALIDATION_ERROR
            raise ApiError(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Validation failed",
                details={"violations": [{"field": "email", "rule": "unique", "message": "Email already exists"}]},
            )

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Роль по умолчанию USER (как обычно делают)
        _USERS_BY_EMAIL[email] = {
            "id": user_id,
            "email": email,
            "password": register_request.password,  # позже заменим на hash в БД
            "role": "USER",
            "created_at": now,
        }

        return UserResponse(
            id=user_id,
            email=email,
            role="USER",
            created_at=now.isoformat(),
        )

    async def login(self, login_request: LoginRequest) -> AuthTokensResponse:
        email = login_request.email.lower().strip()
        user = _USERS_BY_EMAIL.get(email)

        if not user or user["password"] != login_request.password:
            raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Invalid credentials", details=None)

        access = create_access_token(user_id=user["id"], role=user["role"])
        refresh = create_refresh_token(user_id=user["id"], role=user["role"])
        _REFRESH_TOKENS[refresh] = user["id"]

        # expires_in — в секундах (для 20 минут: 1200)
        return AuthTokensResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="Bearer",
            expires_in=20 * 60,
        )

    async def refresh_token(self, refresh_request: RefreshRequest) -> AccessTokenResponse:
        refresh_token = refresh_request.refresh_token

        # Проверим что токен вообще наш
        user_id = _REFRESH_TOKENS.get(refresh_token)
        if not user_id:
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid", details=None)

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid", details=None)

        role = payload.get("role")
        if role not in {"USER", "SELLER", "ADMIN"}:
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid", details=None)

        access = create_access_token(user_id=user_id, role=role)
        return AccessTokenResponse(access_token=access, token_type="Bearer", expires_in=20 * 60)