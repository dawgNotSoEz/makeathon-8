from pydantic import BaseModel, ConfigDict


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: bool = True
    message: str
    code: str
    correlation_id: str


class RootResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    message: str


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    checks: dict[str, str]
