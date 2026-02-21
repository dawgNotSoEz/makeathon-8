from pydantic import BaseModel, ConfigDict, Field


MetadataValue = str | int | float | bool | None


class VectorQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[str] = Field(default_factory=list)
    metadatas: list[dict[str, MetadataValue]] = Field(default_factory=list)
    distances: list[float] = Field(default_factory=list)


class VectorDocumentsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[str] = Field(default_factory=list)
    metadatas: list[dict[str, MetadataValue]] = Field(default_factory=list)


class RetrievedPolicyChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    metadata: dict[str, MetadataValue]
    relevance_score: float = Field(ge=0, le=1)
    industry: str
