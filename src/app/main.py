from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.promo_codes import router as promo_router
from app.errors import ApiError
from app.middlewares.logging import JsonAccessLogMiddleware
from app.middlewares.request_id import RequestIdMiddleware


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

    app.include_router(auth_router)
    app.include_router(products_router)
    app.include_router(orders_router)
    app.include_router(promo_router)

    return app


app = create_app()