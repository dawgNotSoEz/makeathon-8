from fastapi import APIRouter, Depends

from backend.core.container import get_dashboard_service
from backend.core.security import AuthUser, require_roles
from backend.schemas.dashboard import PolicyDetailResponse, PolicyListItem
from backend.services.dashboard_service import DashboardService


router = APIRouter()


@router.get(
    "",
    response_model=list[PolicyListItem],
)
async def get_all_policies(
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")),
) -> list[PolicyListItem]:
    _ = user
    return await service.get_policy_list()


@router.get(
    "/{policy_id}",
    response_model=PolicyDetailResponse,
)
async def get_policy_by_id(
    policy_id: str,
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")),
) -> PolicyDetailResponse:
    _ = user
    return await service.get_policy_by_id(policy_id)
