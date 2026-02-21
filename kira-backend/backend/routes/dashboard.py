from fastapi import APIRouter, Depends

from backend.core.container import get_dashboard_service
from backend.core.security import AuthUser, require_roles
from backend.schemas.dashboard import DashboardSummaryResponse
from backend.services.dashboard_service import DashboardService


router = APIRouter()


@router.get(
    "",
    response_model=DashboardSummaryResponse,
)
async def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")),
) -> DashboardSummaryResponse:
    _ = user
    return await service.compute_summary()


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
async def get_dashboard_summary(
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")),
) -> DashboardSummaryResponse:
    _ = user
    return await service.compute_summary()
