from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr, ValidationError, field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="forbid")

    app_name: str = "Regulatory Intelligence API"
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000
    enable_metrics_endpoint: bool = False

    cors_origins: list[AnyHttpUrl] = Field(default_factory=list)

    llm_provider: Literal["auto", "openai", "gemini", "mega"] = "auto"

    openai_api_key: SecretStr | None = None
    openai_generation_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    gemini_api_key: SecretStr | None = None
    gemini_embedding_model: str = "models/gemini-embedding-001"
    gemini_generation_model: str = "models/gemini-2.5-flash"

    mega_api_key: SecretStr | None = Field(default=None, validation_alias=AliasChoices("MEGA_LLM_API_KEY", "MEGA_API_KEY"))
    mega_api_base_url: str = "https://api.megallm.ai/v1"
    mega_embedding_model: str = "mega-embedding-1"
    mega_generation_model: str = "mega-chat-1"
    mega_generation_fallback_models: list[str] = Field(default_factory=lambda: ["mega-flash", "gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini"])

    llm_timeout_seconds: int = 25
    llm_max_retries: int = 2

    chroma_host: str
    chroma_port: int = 8001
    chroma_ssl: bool = False
    chroma_collection: str = "regulatory_policies"
    chroma_collection_version: str = ""

    redis_url: str
    cache_namespace: str = "kira"
    cache_ttl_seconds: int = 300

    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "kira-backend"
    jwt_audience: str = "kira-clients"

    rate_limit_per_minute: int = 60
    max_request_size_bytes: int = 1048576

    max_retrieval_results: int = 8
    similarity_threshold: float = 0.7

    data_root: Path = Path("backend/data")
    policies_path: Path = Path("backend/data/policies")
    org_data_path: Path = Path("backend/data/org_data.json")

    @field_validator("rate_limit_per_minute")
    @classmethod
    def validate_rate_limit(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("rate_limit_per_minute must be greater than 0")
        return value

    @field_validator("openai_api_key", "gemini_api_key", "mega_api_key", mode="before")
    @classmethod
    def normalize_empty_api_keys(cls, value):
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("max_request_size_bytes")
    @classmethod
    def validate_request_size(cls, value: int) -> int:
        if value < 1024:
            raise ValueError("max_request_size_bytes must be at least 1024")
        return value

    @field_validator("similarity_threshold")
    @classmethod
    def validate_similarity_threshold(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        return value

    @model_validator(mode="after")
    def validate_provider_keys(self) -> "Settings":
        if self.llm_provider == "openai" and self.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "gemini" and self.gemini_api_key is None:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if self.llm_provider == "mega" and self.mega_api_key is None:
            raise ValueError("MEGA_LLM_API_KEY (or MEGA_API_KEY) is required when LLM_PROVIDER=mega")
        if self.llm_provider == "auto" and not any([self.openai_api_key, self.gemini_api_key, self.mega_api_key]):
            raise ValueError("No LLM provider configured. Set OPENAI_API_KEY and/or GEMINI_API_KEY and/or MEGA_LLM_API_KEY")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as error:
        raise RuntimeError(f"Invalid application configuration: {error}") from error


config = get_settings()
