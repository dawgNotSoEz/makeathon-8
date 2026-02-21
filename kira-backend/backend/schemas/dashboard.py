from pydantic import BaseModel, ConfigDict


class CountByType(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    count: int


class CountByStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    count: int


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    totalDocuments: int
    assignedPolicies: int
    reviewedPolicies: int
    pendingPolicies: int
    documentsByType: list[CountByType]
    processingStatus: list[CountByStatus]


class PolicyListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    authority: str
    version: str
    effectiveDate: str
    status: str
    assigned: bool


class PolicySection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: str
    highlight: bool


class PolicyDetailResponse(PolicyListItem):
    content: str
    metadata: dict[str, str | int | float | bool | None]
    sections: list[PolicySection]
