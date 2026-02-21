from collections import Counter

from backend.core.cache import RedisCache
from backend.core.exceptions import NotFoundError
from backend.core.vector_store import VectorStoreClient
from backend.schemas.retrieval import MetadataValue
from backend.schemas.dashboard import (
    CountByStatus,
    CountByType,
    DashboardSummaryResponse,
    PolicyDetailResponse,
    PolicyListItem,
    PolicySection,
)


class DashboardService:
    def __init__(self, vector_store: VectorStoreClient, cache: RedisCache) -> None:
        self.vector_store = vector_store
        self.cache = cache

    async def compute_summary(self) -> DashboardSummaryResponse:
        cache_key = "summary"
        cached = await self.cache.get_json("dashboard", cache_key)
        if cached is not None:
            return DashboardSummaryResponse.model_validate(cached)

        results = await self.vector_store.all_documents(limit=300)
        metadatas = results.metadatas

        authority_count = Counter(m.get("authority", "Unknown") for m in metadatas)
        status_count = Counter(m.get("processing_status", "Processed") for m in metadatas)

        response = DashboardSummaryResponse(
            totalDocuments=len(metadatas),
            assignedPolicies=len(metadatas),
            reviewedPolicies=status_count.get("Processed", 0),
            pendingPolicies=status_count.get("Pending", 0),
            documentsByType=[CountByType(type=name, count=count) for name, count in authority_count.items()],
            processingStatus=[CountByStatus(status=name, count=count) for name, count in status_count.items()],
        )
        await self.cache.set_json("dashboard", cache_key, response.model_dump())
        return response

    async def get_policy_list(self) -> list[PolicyListItem]:
        results = await self.vector_store.all_documents(limit=300)
        metadatas = results.metadatas

        policies: list[PolicyListItem] = []
        for index, metadata in enumerate(metadatas):
            policies.append(
                PolicyListItem(
                    id=str(metadata.get("policy_id", f"policy_{index}")),
                    title=str(metadata.get("policy_name", "Unknown Policy")),
                    authority=str(metadata.get("authority", "Unknown")),
                    version=str(metadata.get("version", "1.0")),
                    effectiveDate=str(metadata.get("effective_date", "")),
                    status=str(metadata.get("processing_status", "Processed")),
                    assigned=True,
                )
            )
        return policies

    async def get_policy_by_id(self, policy_id: str) -> PolicyDetailResponse:
        result = await self.vector_store.policy_by_id(policy_id)
        metadatas = result.metadatas
        documents = result.documents

        if not metadatas:
            raise NotFoundError(f"Policy {policy_id} not found", code="POLICY_NOT_FOUND")

        metadata = metadatas[0]
        content = str(documents[0]) if documents else ""

        return PolicyDetailResponse(
            id=str(metadata.get("policy_id", policy_id)),
            title=str(metadata.get("policy_name", "Unknown Policy")),
            authority=str(metadata.get("authority", "Unknown")),
            version=str(metadata.get("version", "1.0")),
            effectiveDate=str(metadata.get("effective_date", "")),
            status=str(metadata.get("processing_status", "Processed")),
            assigned=True,
            content=content,
            metadata=self._sanitize_metadata(metadata),
            sections=self._parse_sections(content),
        )

    def _sanitize_metadata(self, metadata: dict[str, MetadataValue]) -> dict[str, MetadataValue]:
        clean: dict[str, MetadataValue] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                clean[str(key)] = value
            else:
                clean[str(key)] = str(value)
        return clean

    def _parse_sections(self, content: str) -> list[PolicySection]:
        sections: list[PolicySection] = []
        blocks = [line.strip() for line in content.splitlines() if line.strip()]
        for index, line in enumerate(blocks):
            sections.append(PolicySection(title=f"Section {index + 1}", content=line, highlight=False))
        return sections
