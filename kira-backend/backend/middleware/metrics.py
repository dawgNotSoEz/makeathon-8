import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.metrics import REQUEST_COUNT, REQUEST_DURATION


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        method = request.method
        path = request.url.path
        status_code = str(response.status_code)

        REQUEST_COUNT.labels(method=method, path=path, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, path=path).observe(duration)

        return response
