from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.core.cache import RedisCache
from backend.core.config import config


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > config.max_request_size_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": True,
                    "message": "Request body too large",
                    "code": "REQUEST_TOO_LARGE",
                    "correlation_id": getattr(request.state, "correlation_id", ""),
                },
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache: RedisCache):
        super().__init__(app)
        self.cache = cache

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        count = await self.cache.increment_with_ttl("ratelimit", key, 60)
        if count > config.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "correlation_id": getattr(request.state, "correlation_id", ""),
                },
            )
        return await call_next(request)
