import hashlib

from backend.core.cache import RedisCache
from backend.core.exceptions import UpstreamServiceError
from backend.core.llm_client import LlmClient
from backend.core.rag_pipeline import RegulatoryRAGPipeline
from backend.core.sanitize import sanitize_output_text, validate_prompt_input
from backend.schemas.analysis import OrganizationProfile
from backend.schemas.assistant import AssistantChatResponse


class AssistantService:
    def __init__(self, rag_pipeline: RegulatoryRAGPipeline, llm_client: LlmClient, cache: RedisCache) -> None:
        self.rag_pipeline = rag_pipeline
        self.llm_client = llm_client
        self.cache = cache

    async def chat(self, message: str, organization_profile: OrganizationProfile) -> AssistantChatResponse:
        validate_prompt_input(message)

        cache_key = hashlib.sha256(f"{message}:{organization_profile.model_dump_json()}".encode("utf-8")).hexdigest()
        cached = await self.cache.get_json("assistant", cache_key)
        if cached is not None:
            return AssistantChatResponse.model_validate(cached)

        retrieved = await self.rag_pipeline.retrieve_relevant_context(organization_profile, message)
        context = "\n".join(item.content[:250] for item in retrieved[:4])

        prompt = (
            "You are an Indian Regulatory Intelligence Assistant.\n"
            "You must:\n"
            "- Analyze official Gazette data.\n"
            "- Answer general and specific policy questions.\n"
            "- Avoid hallucinations.\n"
            "- Say \"No verified information found\" if unsure.\n"
            "- Prefer extracted PDF data over external knowledge.\n"
            "- Keep responses concise and factual.\n"
            "Do not fabricate policies or rely on external knowledge when context is provided.\n"
            f"Context: {context}\n"
            f"Question: {message}"
        )
        try:
            reply = sanitize_output_text(await self.llm_client.generate_text(prompt))
        except UpstreamServiceError:
            if context:
                reply = sanitize_output_text(
                    f"Fallback response: based on retrieved policy context, key points include {context[:320]}"
                )
            else:
                reply = sanitize_output_text(
                    "Fallback response: no matching policy context was retrieved. Please refine your question with specific policy identifiers or obligations."
                )

        confidence = "LOW"
        if len(retrieved) >= 3:
            confidence = "HIGH"
        elif len(retrieved) >= 1:
            confidence = "MEDIUM"

        response = AssistantChatResponse(reply=reply, confidence=confidence, context_used=len(retrieved))
        await self.cache.set_json("assistant", cache_key, response.model_dump())
        return response
