import json
import logging
import uuid
from collections import deque
from statistics import median
from time import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from exceptions import AppError

logger = logging.getLogger(__name__)

_response_times: deque[float] = deque(maxlen=1000)


def get_response_time_percentiles() -> dict:
    if not _response_times:
        return {"p50": 0, "p95": 0, "p99": 0}
    sorted_times = sorted(_response_times)
    n = len(sorted_times)
    return {
        "p50": round(median(sorted_times), 2),
        "p95": round(sorted_times[int(n * 0.95)], 2),
        "p99": round(sorted_times[int(n * 0.99)], 2),
    }


def _json_log(level: str, message: str, **extra):
    record = {"level": level, "message": message, **extra}
    log_line = json.dumps(record, default=str)
    getattr(logger, level.lower(), logger.info)(log_line)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request.state.start_time = time()

        _json_log(
            "INFO",
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query),
            client=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        duration = time() - request.state.start_time
        _response_times.append(duration)
        duration_ms = round(duration * 1000, 2)

        log_kwargs = dict(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        if response.status_code >= 500:
            _json_log("ERROR", "Request failed", **log_kwargs)
        elif response.status_code >= 400:
            _json_log("WARNING", "Request warning", **log_kwargs)
        else:
            _json_log("INFO", "Request completed", **log_kwargs)

        response.headers["X-Request-ID"] = request_id
        return response


class AppErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AppError as e:
            _json_log(
                "WARNING",
                "Application error",
                request_id=getattr(request.state, "request_id", None),
                error=e.message,
                status_code=e.status_code,
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.message},
            )


SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
