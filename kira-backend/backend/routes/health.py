from fastapi import APIRouter, Depends

from backend.core.container import get_cache, get_vector_store
from backend.schemas.common import HealthStatus


router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    return HealthStatus(status="ok", checks={"service": "up"})


@router.get("/readiness", response_model=HealthStatus)
async def readiness() -> HealthStatus:
    cache = get_cache()
    vector = get_vector_store()

    redis_ok = await cache.ping()
    await vector.get_collection()

    checks = {
        "redis": "up" if redis_ok else "down",
        "vector_store": "up",
    }
    status = "ready" if redis_ok else "degraded"
    return HealthStatus(status=status, checks=checks)
