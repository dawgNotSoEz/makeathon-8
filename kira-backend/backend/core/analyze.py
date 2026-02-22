import json

from pydantic import ValidationError
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

    @staticmethod
    def _normalize_risk_level(value: object, context_count: int) -> str:
        normalized = str(value or "").strip().upper()
        risk_aliases = {
            "LOW": "LOW",
            "MINOR": "LOW",
            "MEDIUM": "MEDIUM",
            "MODERATE": "MEDIUM",
            "HIGH": "HIGH",
            "SEVERE": "HIGH",
            "CRITICAL": "CRITICAL",
        }
        if normalized in risk_aliases:
            return risk_aliases[normalized]
        if context_count >= 6:
            return "HIGH"
        if context_count >= 3:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _normalize_financial(value: object) -> str:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                return cleaned
        if isinstance(value, dict):
            compact = {str(key): str(val) for key, val in value.items() if str(val).strip()}
            if compact:
                return json.dumps(compact, ensure_ascii=False)
        if isinstance(value, list):
            cleaned_list = [str(item).strip() for item in value if str(item).strip()]
            if cleaned_list:
                return "; ".join(cleaned_list)
        return (
            "Estimated impact: prioritize compliance operations allocation for current review cycle and "
            "track incremental cost exposure against control remediation milestones."
        )

    @staticmethod
    def _fallback_payload(org_profile: OrganizationProfile, context_count: int) -> AnalyzerPayload:
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

    async def generate(self, org_profile: OrganizationProfile, context_count: int) -> AnalyzerPayload:
        prompt = (
            "You are a regulatory impact engine. Return only valid JSON with keys "
            "summary, financial, compliance_risk_level. "
            f"Organization={org_profile.organization_name}, Industry={org_profile.industry}, "
            f"Business Model={org_profile.business_model}, Relevant policy chunks={context_count}."
        )
        try:
            payload = await self.llm.generate_json(prompt)
            normalized_payload = {
                "summary": str(payload.get("summary") or "").strip()
                or (
                    f"Automated analysis for {org_profile.organization_name} in {org_profile.industry}. "
                    f"{context_count} relevant policy chunks were identified for review."
                ),
                "financial": self._normalize_financial(payload.get("financial")),
                "compliance_risk_level": self._normalize_risk_level(payload.get("compliance_risk_level"), context_count),
            }
            return AnalyzerPayload.model_validate(normalized_payload)
        except (UpstreamServiceError, ValidationError, TypeError, AttributeError, KeyError):
            return self._fallback_payload(org_profile, context_count)
