from fastapi import APIRouter, Depends

from backend.core.container import get_dashboard_service
from backend.core.security import AuthUser, require_roles
from backend.core.config import config
from backend.schemas.dashboard import PolicyDetailResponse, PolicyListItem
from backend.services.dashboard_service import DashboardService


router = APIRouter()


@router.get(
    "",
    response_model=list[PolicyListItem],
)
async def get_all_policies(
    service: DashboardService = Depends(get_dashboard_service),
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")) if config.environment != "dev" else Depends(lambda: AuthUser.model_validate({"sub": "dev", "role": "admin", "iss": config.jwt_issuer, "aud": config.jwt_audience, "exp": 9999999999})),
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
    user: AuthUser = Depends(require_roles("admin", "analyst", "user")) if config.environment != "dev" else Depends(lambda: AuthUser.model_validate({"sub": "dev", "role": "admin", "iss": config.jwt_issuer, "aud": config.jwt_audience, "exp": 9999999999})),
) -> PolicyDetailResponse:
    _ = user
    return await service.get_policy_by_id(policy_id)
