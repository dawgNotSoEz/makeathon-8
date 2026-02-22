from fastapi import APIRouter, Depends

from backend.core.config import config
from backend.core.container import get_analysis_service, get_pdf_analyzer_service
from backend.core.security import AuthUser, require_roles
from backend.schemas.analysis import AnalysisRunRequest, AnalysisRunResponse, GrowthPoint, RelevantPolicy
from backend.services.analysis_service import AnalysisService
from backend.services.pdfAnalyzer import PdfAnalyzerService


router = APIRouter()


def _score_from_risk(risk_level: str) -> int:
    normalized = risk_level.strip().lower()
    if normalized == "high":
        return 80
    if normalized == "medium":
        return 60
    return 35


def _impact_level_from_risk(risk_level: str) -> str:
    normalized = risk_level.strip().lower()
    if normalized == "high":
        return "High"
    if normalized == "medium":
        return "Medium"
    return "Low"


def _growth_data(risk_score: int) -> list[GrowthPoint]:
    baseline = 100 - risk_score / 2
    return [
        GrowthPoint(label="Q1", value=round(baseline, 2)),
        GrowthPoint(label="Q2", value=round(baseline + 3, 2)),
        GrowthPoint(label="Q3", value=round(baseline + 6, 2)),
        GrowthPoint(label="Q4", value=round(baseline + 9, 2)),
    ]


@router.post(
    "/run",
    response_model=AnalysisRunResponse,
)
async def run_analysis(
    request: AnalysisRunRequest,
    service: AnalysisService = Depends(get_analysis_service),
    pdf_analyzer: PdfAnalyzerService = Depends(get_pdf_analyzer_service),
    user: AuthUser = Depends(require_roles("admin", "analyst"))
    if config.environment != "dev"
    else Depends(
        lambda: AuthUser.model_validate(
            {
                "sub": "dev",
                "role": "admin",
                "iss": config.jwt_issuer,
                "aud": config.jwt_audience,
                "exp": 9999999999,
            }
        )
    ),
) -> AnalysisRunResponse:
    _ = user
    if request.gazetteId:
        gazette_result = await pdf_analyzer.analyze_gazette(request.gazetteId)
        analysis = gazette_result.get("analysis") if isinstance(gazette_result, dict) else None
        if isinstance(analysis, dict):
            policy_name = str(analysis.get("policy_name") or gazette_result.get("subject") or request.gazetteId)
            ministry = str(analysis.get("ministry") or "Unknown ministry")
            policy_type = str(analysis.get("policy_type") or "Unknown type")
            risk_level = str(analysis.get("risk_level") or "Low")
            actions = analysis.get("compliance_actions_required") or []
            penalties = str(analysis.get("penalties") or "Not specified")

            summary = f"{policy_name} issued by {ministry} ({policy_type})."
            if gazette_result.get("url"):
                summary = f"{summary} Source: {gazette_result.get('url')}"

            financial_projection = "Compliance actions: "
            if isinstance(actions, list) and actions:
                financial_projection += "; ".join([str(item) for item in actions[:4]])
            else:
                financial_projection += "Not specified"
            financial_projection += f". Penalties: {penalties}."

            risk_score = _score_from_risk(risk_level)
            return AnalysisRunResponse(
                relevantPolicies=[RelevantPolicy(id=request.gazetteId, impactLevel=_impact_level_from_risk(risk_level))],
                impactSummary=summary,
                financialImpactProjection=financial_projection,
                riskScore=risk_score,
                growthChartData=_growth_data(risk_score),
            )

    return await service.run_impact_analysis(request.organizationProfile)
