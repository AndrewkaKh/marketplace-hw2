from fastapi import APIRouter, status

from app.db.session import db_session
from app.services.auth_service import AuthService
from marketplace_gen.models.access_token_response import AccessTokenResponse
from marketplace_gen.models.auth_tokens_response import AuthTokensResponse
from marketplace_gen.models.login_request import LoginRequest
from marketplace_gen.models.refresh_request import RefreshRequest
from marketplace_gen.models.register_request import RegisterRequest
from marketplace_gen.models.user_response import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> UserResponse:
    db = next(db_session())
    try:
        return AuthService(db).register(payload)
    finally:
        db.close()


@router.post("/login", response_model=AuthTokensResponse, status_code=status.HTTP_200_OK)
async def login(payload: LoginRequest) -> AuthTokensResponse:
    db = next(db_session())
    try:
        return AuthService(db).login(payload)
    finally:
        db.close()


@router.post("/refresh", response_model=AccessTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(payload: RefreshRequest) -> AccessTokenResponse:
    db = next(db_session())
    try:
        return AuthService(db).refresh(payload)
    finally:
        db.close()