from fastapi import APIRouter, Depends

from backend.core.container import get_analysis_service
from backend.core.security import AuthUser, require_roles
from backend.schemas.analysis import AnalysisRunRequest, AnalysisRunResponse
from backend.services.analysis_service import AnalysisService


router = APIRouter()


@router.post(
    "/run",
    response_model=AnalysisRunResponse,
)
async def run_analysis(
    request: AnalysisRunRequest,
    service: AnalysisService = Depends(get_analysis_service),
    user: AuthUser = Depends(require_roles("admin", "analyst")),
) -> AnalysisRunResponse:
    _ = user
    return await service.run_impact_analysis(request.organizationProfile)
