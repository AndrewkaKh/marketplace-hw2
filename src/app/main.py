from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import ApiError
from app.middlewares.logging import JsonAccessLogMiddleware
from app.middlewares.request_id import RequestIdMiddleware
from app.security.jwt import bearer_auth_dependency
import impl


def create_app() -> FastAPI:
    app = FastAPI(title="Marketplace API")

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(JsonAccessLogMiddleware)

    @app.exception_handler(ApiError)
    async def api_error_handler(_, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_, exc: RequestValidationError):
        violations = []
        for e in exc.errors():
            loc = ".".join(str(x) for x in e.get("loc", []) if x != "body")
            violations.append(
                {
                    "field": loc or "body",
                    "rule": e.get("type", "validation"),
                    "message": e.get("msg", "Invalid value"),
                }
            )
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"violations": violations},
            },
        )

    from marketplace_gen.apis.auth_api import router as auth_router
    from marketplace_gen.apis.products_api import router as products_router
    from marketplace_gen.apis.orders_api import router as orders_router
    from marketplace_gen.apis.promo_codes_api import router as promo_router

    app.include_router(auth_router)
    app.include_router(products_router)
    app.include_router(orders_router)
    app.include_router(promo_router)

    # Override generated security dependency (bearerAuth)
    from marketplace_gen import security_api as gen_security

    # Обычно генератор делает get_token_bearerAuth
    token_dep = getattr(gen_security, "get_token_bearerAuth", None) or getattr(
        gen_security, "get_token_bearer_auth", None
    )
    if token_dep is not None:
        app.dependency_overrides[token_dep] = bearer_auth_dependency

    return app


app = create_app()