from pydantic import BaseModel, ConfigDict, Field


class OrganizationProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_name: str = Field(min_length=2, max_length=120)
    industry: str = Field(min_length=2, max_length=80)
    business_model: str = Field(min_length=2, max_length=120)
    sub_sector: str | None = Field(default=None, max_length=80)


class AnalysisRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organizationProfile: OrganizationProfile


class RelevantPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    impactLevel: str = Field(pattern=r"^(High|Medium|Low)$")


class GrowthPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: float


class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relevantPolicies: list[RelevantPolicy]
    impactSummary: str
    financialImpactProjection: str
    riskScore: int = Field(ge=0, le=100)
    growthChartData: list[GrowthPoint]
