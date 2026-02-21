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
        self.provider = config.llm_provider
        self.client = None
        if self.provider == "gemini":
            self.client = genai.Client(api_key=config.gemini_api_key.get_secret_value())
        elif self.provider == "mega":
            if config.mega_api_key is None:
                raise UpstreamServiceError("Mega API key is not configured", code="MEGA_KEY_MISSING")
            self.client = AsyncOpenAI(
                base_url=config.mega_api_base_url,
                api_key=config.mega_api_key.get_secret_value(),
                timeout=config.llm_timeout_seconds,
            )

    async def generate_embedding(self, text: str) -> list[float]:
        async def _run() -> list[float]:
            if self.provider == "gemini":
                result = await asyncio.to_thread(
                    self.client.models.embed_content,
                    model=config.gemini_embedding_model,
                    contents=text,
                )
                return result.embeddings[0].values

            try:
                response = await self.client.embeddings.create(
                    model=config.mega_embedding_model,
                    input=text,
                )
                return [float(v) for v in response.data[0].embedding]
            except Exception as exc:
                raise UpstreamServiceError(f"Mega embedding request failed: {exc}", code="MEGA_API_ERROR") from exc

        return await self._with_retry_and_timeout(_run, operation_name="embedding")

    async def generate_text(self, prompt: str) -> str:
        async def _run() -> str:
            if self.provider == "gemini":
                result = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=config.gemini_generation_model,
                    contents=prompt,
                )
                if not result.text:
                    raise UpstreamServiceError("LLM returned empty response", code="LLM_EMPTY_RESPONSE")
                return result.text

            candidate_models: list[str] = [config.mega_generation_model]
            for fallback_model in config.mega_generation_fallback_models:
                if fallback_model not in candidate_models:
                    candidate_models.append(fallback_model)

            last_error: Exception | None = None
            for model_name in candidate_models:
                try:
                    response = await self.client.chat.completions.create(
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
                            extra={"extra": {"primary_model": config.mega_generation_model, "used_model": model_name}},
                        )
                    return str(content)
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "llm_generation_model_attempt_failed",
                        extra={"extra": {"model": model_name}},
                        exc_info=True,
                    )

            raise UpstreamServiceError(f"Mega chat request failed: {last_error}", code="MEGA_API_ERROR") from last_error

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
