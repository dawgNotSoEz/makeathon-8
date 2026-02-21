from pydantic import BaseModel, ConfigDict, Field

from backend.core.exceptions import UpstreamServiceError
from backend.core.llm_client import LlmClient
from backend.schemas.analysis import OrganizationProfile


class AnalyzerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    financial: str
    compliance_risk_level: str = Field(pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")


class RegulatoryImpactAnalyzer:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm = llm_client

    async def generate(self, org_profile: OrganizationProfile, context_count: int) -> AnalyzerPayload:
        prompt = (
            "You are a regulatory impact engine. Return only valid JSON with keys "
            "summary, financial, compliance_risk_level. "
            f"Organization={org_profile.organization_name}, Industry={org_profile.industry}, "
            f"Business Model={org_profile.business_model}, Relevant policy chunks={context_count}."
        )
        try:
            payload = await self.llm.generate_json(prompt)
            return AnalyzerPayload.model_validate(payload)
        except UpstreamServiceError:
            risk = "LOW"
            if context_count >= 6:
                risk = "HIGH"
            elif context_count >= 3:
                risk = "MEDIUM"

            return AnalyzerPayload(
                summary=(
                    f"Automated fallback analysis for {org_profile.organization_name} in {org_profile.industry}. "
                    f"{context_count} relevant policy chunks were identified for review."
                ),
                financial=(
                    "Estimated impact: prioritize compliance operations allocation for current review cycle and "
                    "track incremental cost exposure against control remediation milestones."
                ),
                compliance_risk_level=risk,
            )
