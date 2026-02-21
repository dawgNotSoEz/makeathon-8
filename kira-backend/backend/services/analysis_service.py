import hashlib

from backend.core.analyze import RegulatoryImpactAnalyzer
from backend.core.cache import RedisCache
from backend.core.rag_pipeline import RegulatoryRAGPipeline
from backend.schemas.analysis import AnalysisRunResponse, GrowthPoint, OrganizationProfile, RelevantPolicy


class AnalysisService:
    def __init__(self, rag_pipeline: RegulatoryRAGPipeline, analyzer: RegulatoryImpactAnalyzer, cache: RedisCache) -> None:
        self.rag_pipeline = rag_pipeline
        self.analyzer = analyzer
        self.cache = cache

    async def run_impact_analysis(self, organization_profile: OrganizationProfile) -> AnalysisRunResponse:
        cache_key = hashlib.sha256(organization_profile.model_dump_json().encode("utf-8")).hexdigest()
        cached = await self.cache.get_json("analysis", cache_key)
        if cached is not None:
            cached_response = AnalysisRunResponse.model_validate(cached)
            if cached_response.relevantPolicies:
                return cached_response

        retrieval = await self.rag_pipeline.retrieve_relevant_context(
            organization_profile,
            query="regulatory compliance impact requirements",
        )

        relevant = [
            RelevantPolicy(
                id=str(item.metadata.get("policy_id", "")),
                impactLevel=self._impact_level(str(item.metadata.get("authority", "Unknown"))),
            )
            for item in retrieval[:5]
        ]

        analysis_payload = await self.analyzer.generate(organization_profile, context_count=len(retrieval))
        risk_score = self._risk_score(analysis_payload.compliance_risk_level, len(relevant))

        response = AnalysisRunResponse(
            relevantPolicies=relevant,
            impactSummary=analysis_payload.summary,
            financialImpactProjection=analysis_payload.financial,
            riskScore=risk_score,
            growthChartData=self._growth_data(risk_score),
        )

        await self.cache.set_json("analysis", cache_key, response.model_dump())
        return response

    def _impact_level(self, authority: str) -> str:
        if authority in {"RBI", "SEBI"}:
            return "High"
        if authority in {"IRDAI"}:
            return "Medium"
        return "Low"

    def _risk_score(self, compliance_risk_level: str, policy_count: int) -> int:
        base = {"LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 90}[compliance_risk_level]
        score = min(100, base + min(policy_count * 2, 10))
        return score

    def _growth_data(self, risk_score: int) -> list[GrowthPoint]:
        baseline = 100 - risk_score / 2
        return [
            GrowthPoint(label="Q1", value=round(baseline, 2)),
            GrowthPoint(label="Q2", value=round(baseline + 3, 2)),
            GrowthPoint(label="Q3", value=round(baseline + 6, 2)),
            GrowthPoint(label="Q4", value=round(baseline + 9, 2)),
        ]
