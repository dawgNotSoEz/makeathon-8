from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import config
from backend.core.container import get_cache
from backend.core.error_handlers import register_exception_handlers
from backend.core.logging_config import setup_logging
from backend.middleware.limits import RateLimitMiddleware, RequestSizeLimitMiddleware
from backend.middleware.metrics import MetricsMiddleware
from backend.middleware.request_context import CorrelationIdMiddleware, RequestLoggingMiddleware
from backend.routes import analysis, assistant, dashboard, gazettes, health, metrics, policy_query, registry
from backend.schemas.common import RootResponse


setup_logging(config.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = get_cache()
    await cache.ping()
    yield
    await cache.close()


app = FastAPI(title=config.app_name, lifespan=lifespan)

allowed_origins = [str(origin) for origin in config.cors_origins]
if config.environment == "dev":
    for dev_origin in (
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ):
        if dev_origin not in allowed_origins:
            allowed_origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware, cache=get_cache())
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

register_exception_handlers(app)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(health.router, prefix="", tags=["health"])
if config.enable_metrics_endpoint:
    app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(registry.router, prefix="/api/policies", tags=["policies"])
app.include_router(gazettes.router, prefix="/api", tags=["gazettes"])
app.include_router(policy_query.router, prefix="/api", tags=["policy-query"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])


@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(status="running", message=config.app_name)
