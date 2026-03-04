import json
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.security.context import get_current_user


def _mask_sensitive(body: object) -> object:
    if isinstance(body, dict):
        masked = {}
        for k, v in body.items():
            if k.lower() in {"password", "pass", "pwd"}:
                masked[k] = "***"
            else:
                masked[k] = _mask_sensitive(v)
        return masked
    if isinstance(body, list):
        return [_mask_sensitive(x) for x in body]
    return body


class JsonAccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = time.time()

        req_body_obj = None
        if request.method in {"POST", "PUT", "DELETE"}:
            raw = await request.body()
            if raw:
                try:
                    req_body_obj = _mask_sensitive(json.loads(raw.decode("utf-8")))
                except Exception:
                    req_body_obj = {"_raw": raw[:2048].decode("utf-8", errors="replace")}

        response: Response = await call_next(request)

        duration_ms = int((time.time() - started) * 1000)
        user = get_current_user()
        request_id = getattr(request.state, "request_id", None)

        log_obj = {
            "request_id": request_id,
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": (user.user_id if user else None),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if req_body_obj is not None:
            log_obj["request_body"] = req_body_obj

        print(json.dumps(log_obj, ensure_ascii=False))
        return response