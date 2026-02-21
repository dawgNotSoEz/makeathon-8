from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.analysis import OrganizationProfile


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=3, max_length=2000)
    organizationProfile: OrganizationProfile


class AssistantChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str
    confidence: str = Field(pattern=r"^(LOW|MEDIUM|HIGH)$")
    context_used: int = Field(ge=0)
