import asyncio
import json
import logging
import time

import google.genai as genai
from openai import AsyncOpenAI

from backend.core.config import config
from backend.core.exceptions import UpstreamServiceError
from backend.core.metrics import LLM_OPERATION_DURATION, LLM_OPERATION_FAILURES


logger = logging.getLogger(__name__)


class LlmClient:
    def __init__(self) -> None:
        self.gemini_client = (
            genai.Client(api_key=config.gemini_api_key.get_secret_value()) if config.gemini_api_key is not None else None
        )
        self.openai_client = None
        if config.openai_api_key is not None:
            openai_key = config.openai_api_key.get_secret_value()
            self.openai_client = AsyncOpenAI(
                api_key=openai_key,
                timeout=config.llm_timeout_seconds,
                default_headers=self._build_auth_headers(openai_key),
            )

        self.mega_client = None
        if config.mega_api_key is not None:
            mega_key = config.mega_api_key.get_secret_value()
            self.mega_client = AsyncOpenAI(
                base_url=config.mega_api_base_url,
                api_key=mega_key,
                timeout=config.llm_timeout_seconds,
                default_headers=self._build_auth_headers(mega_key),
            )

    def get_llm_provider(self) -> str:
        if config.llm_provider != "auto":
            return config.llm_provider
        if config.openai_api_key:
            return "openai"
        if config.gemini_api_key:
            return "gemini"
        if config.mega_api_key:
            return "mega"
        raise UpstreamServiceError("No LLM provider configured", code="LLM_PROVIDER_MISSING")

    @staticmethod
    def _build_auth_headers(api_key: str) -> dict[str, str]:
        if not api_key:
            raise UpstreamServiceError("OPENAI_API_KEY is not set", code="OPENAI_KEY_MISSING")
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _provider_order(self, primary_provider: str) -> list[str]:
        providers = [primary_provider]
        for candidate in ("openai", "gemini", "mega"):
            if candidate == primary_provider:
                continue
            if self._provider_available(candidate):
                providers.append(candidate)
        return providers

    def _provider_available(self, provider: str) -> bool:
        if provider == "openai":
            return self.openai_client is not None
        if provider == "gemini":
            return self.gemini_client is not None
        if provider == "mega":
            return self.mega_client is not None
        return False

    async def generate_embedding(self, text: str) -> list[float]:
        async def _run() -> list[float]:
            primary_provider = self.get_llm_provider()
            last_error: Exception | None = None
            for provider in self._provider_order(primary_provider):
                try:
                    if provider == "openai":
                        if config.openai_api_key is None:
                            raise UpstreamServiceError("OPENAI_API_KEY is not set", code="OPENAI_KEY_MISSING")
                        response = await self.openai_client.embeddings.create(
                            model=config.openai_embedding_model,
                            input=text,
                        )
                        return [float(v) for v in response.data[0].embedding]
                    if provider == "gemini":
                        if config.gemini_api_key is None:
                            raise UpstreamServiceError("GEMINI_API_KEY is not set", code="GEMINI_KEY_MISSING")
                        result = await asyncio.to_thread(
                            self.gemini_client.models.embed_content,
                            model=config.gemini_embedding_model,
                            contents=text,
                        )
                        return result.embeddings[0].values
                    if provider == "mega":
                        if config.mega_api_key is None:
                            raise UpstreamServiceError("MEGA_LLM_API_KEY is not set", code="MEGA_KEY_MISSING")
                        response = await self.mega_client.embeddings.create(
                            model=config.mega_embedding_model,
                            input=text,
                        )
                        return [float(v) for v in response.data[0].embedding]
                except Exception as exc:
                    last_error = exc
                    logger.warning("llm_embedding_provider_failed", extra={"extra": {"provider": provider}}, exc_info=True)

            raise UpstreamServiceError(f"All embedding providers failed: {last_error}", code="LLM_ALL_PROVIDERS_FAILED") from last_error

        return await self._with_retry_and_timeout(_run, operation_name="embedding")

    async def generate_text(self, prompt: str) -> str:
        async def _run() -> str:
            primary_provider = self.get_llm_provider()
            last_error: Exception | None = None

            for provider in self._provider_order(primary_provider):
                try:
                    if provider == "openai":
                        if config.openai_api_key is None:
                            raise UpstreamServiceError("OPENAI_API_KEY is not set", code="OPENAI_KEY_MISSING")
                        response = await self.openai_client.chat.completions.create(
                            model=config.openai_generation_model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                        )
                        content = response.choices[0].message.content
                        if not content:
                            raise UpstreamServiceError("LLM returned empty response", code="LLM_EMPTY_RESPONSE")
                        return str(content)

                    if provider == "gemini":
                        if config.gemini_api_key is None:
                            raise UpstreamServiceError("GEMINI_API_KEY is not set", code="GEMINI_KEY_MISSING")
                        result = await asyncio.to_thread(
                            self.gemini_client.models.generate_content,
                            model=config.gemini_generation_model,
                            contents=prompt,
                        )
                        if not result.text:
                            raise UpstreamServiceError("LLM returned empty response", code="LLM_EMPTY_RESPONSE")
                        return result.text

                    if provider == "mega":
                        if config.mega_api_key is None:
                            raise UpstreamServiceError("MEGA_LLM_API_KEY is not set", code="MEGA_KEY_MISSING")
                        candidate_models: list[str] = [config.mega_generation_model]
                        for fallback_model in config.mega_generation_fallback_models:
                            if fallback_model not in candidate_models:
                                candidate_models.append(fallback_model)

                        model_error: Exception | None = None
                        for model_name in candidate_models:
                            try:
                                response = await self.mega_client.chat.completions.create(
                                    model=model_name,
                                    messages=[{"role": "user", "content": prompt}],
                                    temperature=0.2,
                                )
                                content = response.choices[0].message.content
                                if not content:
                                    raise UpstreamServiceError("LLM returned empty response", code="LLM_EMPTY_RESPONSE")
                                if model_name != config.mega_generation_model:
                                    logger.warning(
                                        "llm_generation_model_fallback_used",
                                        extra={
                                            "extra": {
                                                "primary_model": config.mega_generation_model,
                                                "used_model": model_name,
                                            }
                                        },
                                    )
                                return str(content)
                            except Exception as exc:
                                model_error = exc
                                logger.warning(
                                    "llm_generation_model_attempt_failed",
                                    extra={"extra": {"model": model_name}},
                                    exc_info=True,
                                )
                        raise UpstreamServiceError(f"Mega chat request failed: {model_error}", code="MEGA_API_ERROR") from model_error

                except Exception as exc:
                    last_error = exc
                    logger.error(
                        "llm_provider_failed_switching",
                        exc_info=True,
                        extra={"extra": {"provider": provider}},
                    )

            raise UpstreamServiceError(f"All LLM providers failed: {last_error}", code="LLM_ALL_PROVIDERS_FAILED") from last_error

        return await self._with_retry_and_timeout(_run, operation_name="generation")

    async def generate_json(self, prompt: str) -> dict[str, object]:
        text = await self.generate_text(prompt)
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as exc:
            raise UpstreamServiceError("LLM response is not valid JSON", code="LLM_JSON_PARSE_ERROR") from exc

    async def _with_retry_and_timeout(self, func, operation_name: str):
        last_exc: Exception | None = None
        for attempt in range(config.llm_max_retries + 1):
            start = time.perf_counter()
            try:
                result = await asyncio.wait_for(func(), timeout=config.llm_timeout_seconds)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                LLM_OPERATION_DURATION.labels(operation=operation_name).observe((time.perf_counter() - start))
                logger.info(
                    "llm_operation_success",
                    extra={"extra": {"operation": operation_name, "attempt": attempt + 1, "duration_ms": duration_ms}},
                )
                return result
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                LLM_OPERATION_DURATION.labels(operation=operation_name).observe((time.perf_counter() - start))
                LLM_OPERATION_FAILURES.labels(operation=operation_name).inc()
                logger.error(
                    "llm_operation_failed",
                    exc_info=True,
                    extra={"extra": {"operation": operation_name, "attempt": attempt + 1, "duration_ms": duration_ms}},
                )
                last_exc = exc
                if attempt < config.llm_max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
        raise UpstreamServiceError(f"LLM {operation_name} failed after retries", code="LLM_RETRY_EXHAUSTED") from last_exc
