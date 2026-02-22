from fastapi import APIRouter, Depends

from backend.core.container import get_dashboard_service
from backend.core.security import AuthUser, require_roles
from backend.core.config import config
from backend.schemas.dashboard import DashboardSummaryResponse
from backend.services.dashboard_service import DashboardService


router = APIRouter()


@router.get(
    "",
    response_model=DashboardSummaryResponse,
)
async def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")) if config.environment != "dev" else Depends(lambda: AuthUser.model_validate({"sub": "dev", "role": "admin", "iss": config.jwt_issuer, "aud": config.jwt_audience, "exp": 9999999999})),
) -> DashboardSummaryResponse:
    _ = user
    return await service.compute_summary()


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
async def get_dashboard_summary(
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")) if config.environment != "dev" else Depends(lambda: AuthUser.model_validate({"sub": "dev", "role": "admin", "iss": config.jwt_issuer, "aud": config.jwt_audience, "exp": 9999999999})),
) -> DashboardSummaryResponse:
    _ = user
    return await service.compute_summary()
