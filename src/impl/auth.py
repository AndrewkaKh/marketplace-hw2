from __future__ import annotations

from app.db.session import db_session
from app.services.auth_service import AuthService
from generated.src.marketplace_gen.apis.auth_api_base import BaseAuthApi
from generated.src.marketplace_gen.models.access_token_response import AccessTokenResponse
from generated.src.marketplace_gen.models.auth_tokens_response import AuthTokensResponse
from generated.src.marketplace_gen.models.login_request import LoginRequest
from generated.src.marketplace_gen.models.refresh_request import RefreshRequest
from generated.src.marketplace_gen.models.register_request import RegisterRequest
from generated.src.marketplace_gen.models.user_response import UserResponse

class AuthApiImpl(BaseAuthApi):
    async def register(self, register_request: RegisterRequest) -> UserResponse:
        db = next(db_session())
        try:
            return AuthService(db).register(register_request)
        finally:
            db.close()

    async def login(self, login_request: LoginRequest) -> AuthTokensResponse:
        db = next(db_session())
        try:
            return AuthService(db).login(login_request)
        finally:
            db.close()

    async def refresh_token(self, refresh_request: RefreshRequest) -> AccessTokenResponse:
        db = next(db_session())
        try:
            return AuthService(db).refresh(refresh_request)
        finally:
            db.close()