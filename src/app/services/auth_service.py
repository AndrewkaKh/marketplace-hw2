from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User, UserRole
from app.errors import ApiError
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.passwords import hash_password, verify_password
from app.settings import settings
from marketplace_gen.models.access_token_response import AccessTokenResponse
from marketplace_gen.models.auth_tokens_response import AuthTokensResponse
from marketplace_gen.models.login_request import LoginRequest
from marketplace_gen.models.refresh_request import RefreshRequest
from marketplace_gen.models.register_request import RegisterRequest
from marketplace_gen.models.role import Role
from marketplace_gen.models.user_response import UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: RegisterRequest) -> UserResponse:
        email = payload.email.lower().strip()

        existing = self.db.scalar(select(User).where(User.email == email))
        if existing:
            raise ApiError(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Validation failed",
                details={"violations": [{"field": "email", "rule": "unique", "message": "Email already exists"}]},
            )

        user = User(email=email, password_hash=hash_password(payload.password), role=UserRole.USER)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return UserResponse(
            id=user.id,
            email=user.email,
            role=Role(user.role.value),
            created_at=user.created_at,
        )

    def login(self, payload: LoginRequest) -> AuthTokensResponse:
        email = payload.email.lower().strip()

        user = self.db.scalar(select(User).where(User.email == email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise ApiError(status_code=401, error_code="TOKEN_INVALID", message="Invalid credentials")

        access = create_access_token(user_id=user.id, role=user.role.value)
        refresh = create_refresh_token(user_id=user.id, role=user.role.value)

        refresh_row = RefreshToken(
            user_id=user.id,
            token=refresh,
            revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
        )
        self.db.add(refresh_row)
        self.db.commit()

        return AuthTokensResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="Bearer",
            expires_in=settings.access_token_minutes * 60,
        )

    def refresh(self, payload: RefreshRequest) -> AccessTokenResponse:
        refresh_row = self.db.scalar(select(RefreshToken).where(RefreshToken.token == payload.refresh_token))
        if not refresh_row or refresh_row.revoked:
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid")

        if refresh_row.expires_at < datetime.now(timezone.utc):
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid")

        token_payload = decode_token(payload.refresh_token)
        if token_payload.get("type") != "refresh":
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid")

        user = self.db.get(User, refresh_row.user_id)
        if not user:
            raise ApiError(status_code=401, error_code="REFRESH_TOKEN_INVALID", message="Refresh token invalid")

        access = create_access_token(user_id=user.id, role=user.role.value)
        return AccessTokenResponse(
            access_token=access,
            token_type="Bearer",
            expires_in=settings.access_token_minutes * 60,
        )