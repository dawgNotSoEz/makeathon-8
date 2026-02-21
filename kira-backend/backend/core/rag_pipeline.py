import logging
import re

from backend.core.config import config
from backend.core.llm_client import LlmClient
from backend.core.vector_store import VectorStoreClient
from backend.schemas.analysis import OrganizationProfile
from backend.schemas.retrieval import RetrievedPolicyChunk


logger = logging.getLogger(__name__)


class RegulatoryRAGPipeline:
    def __init__(self, llm_client: LlmClient, vector_client: VectorStoreClient) -> None:
        self.llm = llm_client
        self.vector = vector_client

    async def retrieve_relevant_context(self, org_profile: OrganizationProfile, query: str) -> list[RetrievedPolicyChunk]:
        logger.info("embedding_retrieval_disabled_using_keyword_fallback")
        return await self._keyword_fallback(org_profile, query)

    async def _keyword_fallback(self, org_profile: OrganizationProfile, query: str) -> list[RetrievedPolicyChunk]:
        docs = await self.vector.all_documents(limit=max(config.max_retrieval_results * 10, 100))
        terms = [
            token
            for token in re.findall(r"[a-zA-Z0-9]+", f"{query} {org_profile.industry} {org_profile.business_model}".lower())
            if len(token) >= 3
        ]
        term_set = set(terms)

        scored_items: list[tuple[float, str, dict[str, object]]] = []
        for idx, content in enumerate(docs.documents):
            text = content.lower()
            matches = sum(1 for term in term_set if term in text)
            if matches == 0:
                continue
            score = min(matches / max(len(term_set), 1), 1.0)
            metadata = docs.metadatas[idx] if idx < len(docs.metadatas) else {}
            if metadata.get("authority") is None:
                metadata["authority"] = "Unknown"
            scored_items.append((score, content, metadata))

        scored_items.sort(key=lambda item: item[0], reverse=True)
        selected = scored_items[: config.max_retrieval_results]

        relevant = [
            RetrievedPolicyChunk(
                content=content,
                metadata=metadata,
                relevance_score=score,
                industry=org_profile.industry,
            )
            for score, content, metadata in selected
        ]
        logger.info("keyword_retrieval_completed", extra={"extra": {"result_count": len(relevant)}})
        return relevant
