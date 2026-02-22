from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=2000)
    gazette_id: str | None = None


class PolicyQueryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    answer: str | None = None
    error: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)


class PolicyAnalysisItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    gazette_id: str | None = None
    subject: str | None = None
    url: str | None = None
    analysis: dict[str, Any] | None = None
    fallback_text: str | None = None
    error: str | None = None
