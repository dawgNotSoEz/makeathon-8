import asyncio
import json
import logging
import time
from pathlib import Path

import chromadb

from backend.core.config import config
from backend.core.exceptions import DependencyError
from backend.core.metrics import VECTOR_QUERY_DURATION
from backend.schemas.retrieval import VectorDocumentsResponse, VectorQueryResponse


logger = logging.getLogger(__name__)


class VectorStoreClient:
    def __init__(self) -> None:
        if not config.chroma_host:
            raise DependencyError("CHROMA_HOST is required", code="CHROMA_HOST_MISSING")
        self.client = chromadb.HttpClient(host=config.chroma_host, port=config.chroma_port, ssl=config.chroma_ssl)

    def _collection_name(self) -> str:
        version = config.chroma_collection_version.strip()
        if not version:
            return config.chroma_collection
        return f"{config.chroma_collection}_{version}"

    async def get_collection(self):
        try:
            return await asyncio.to_thread(self.client.get_collection, self._collection_name())
        except Exception as exc:
            raise DependencyError("Unable to connect to Chroma collection", code="VECTOR_COLLECTION_UNAVAILABLE") from exc

    async def query(self, query_embedding: list[float], top_k: int) -> VectorQueryResponse:
        collection = await self.get_collection()
        start = time.perf_counter()
        raw = await asyncio.to_thread(
            collection.query,
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        VECTOR_QUERY_DURATION.labels(operation="query").observe(time.perf_counter() - start)
        logger.info(
            "vector_query_completed",
            extra={"extra": {"duration_ms": round((time.perf_counter() - start) * 1000, 2), "top_k": top_k}},
        )
        return VectorQueryResponse(
            documents=[str(doc) for doc in (raw.get("documents", [[]])[0] if raw.get("documents") else [])],
            metadatas=[m if isinstance(m, dict) else {} for m in (raw.get("metadatas", [[]])[0] if raw.get("metadatas") else [])],
            distances=[float(distance) for distance in (raw.get("distances", [[]])[0] if raw.get("distances") else [])],
        )

    async def all_documents(self, limit: int = 200) -> VectorDocumentsResponse:
        try:
            collection = await self.get_collection()
            raw = await asyncio.to_thread(collection.get, include=["metadatas", "documents"], limit=limit)
            response = VectorDocumentsResponse(
                documents=[str(doc) for doc in raw.get("documents", [])],
                metadatas=[m if isinstance(m, dict) else {} for m in raw.get("metadatas", [])],
            )
            if response.documents:
                return response
            logger.info("vector_store_empty_using_filesystem_fallback")
        except DependencyError:
            logger.warning("vector_store_unavailable_using_filesystem_fallback")
        except Exception:
            logger.warning("vector_store_error_using_filesystem_fallback", exc_info=True)

        filesystem = await asyncio.to_thread(self._load_filesystem_documents)
        return VectorDocumentsResponse(
            documents=filesystem.documents[:limit],
            metadatas=filesystem.metadatas[:limit],
        )

    async def policy_by_id(self, policy_id: str) -> VectorDocumentsResponse:
        try:
            collection = await self.get_collection()
            raw = await asyncio.to_thread(collection.get, where={"policy_id": policy_id}, include=["metadatas", "documents"])
            response = VectorDocumentsResponse(
                documents=[str(doc) for doc in raw.get("documents", [])],
                metadatas=[m if isinstance(m, dict) else {} for m in raw.get("metadatas", [])],
            )
            if response.documents:
                return response
            logger.info("policy_not_found_in_vector_store_using_filesystem_fallback", extra={"extra": {"policy_id": policy_id}})
        except DependencyError:
            logger.warning("vector_store_unavailable_using_filesystem_fallback")
        except Exception:
            logger.warning("vector_store_error_using_filesystem_fallback", exc_info=True)

        fallback = await asyncio.to_thread(self._load_filesystem_documents)
        matched_documents: list[str] = []
        matched_metadatas: list[dict[str, object]] = []
        for idx, metadata in enumerate(fallback.metadatas):
            if str(metadata.get("policy_id", "")) != policy_id:
                continue
            if idx < len(fallback.documents):
                matched_documents.append(fallback.documents[idx])
                matched_metadatas.append(metadata)

        return VectorDocumentsResponse(documents=matched_documents, metadatas=matched_metadatas)

    def _load_filesystem_documents(self) -> VectorDocumentsResponse:
        policies_root = Path(config.policies_path)
        if not policies_root.exists():
            return VectorDocumentsResponse(documents=[], metadatas=[])

        documents: list[str] = []
        metadatas: list[dict[str, object]] = []
        consumed_txt_paths: set[Path] = set()

        for metadata_path in sorted(policies_root.rglob("metadata.json")):
            metadata_raw = self._read_json(metadata_path)
            policy_dir = metadata_path.parent

            selected_txt: Path | None = None
            selected_version = str(metadata_raw.get("last_processed_version", "")).strip()
            if selected_version:
                candidate = policy_dir / f"{selected_version}.txt"
                if candidate.exists():
                    selected_txt = candidate

            if selected_txt is None:
                txt_candidates = sorted(policy_dir.glob("*.txt"))
                if txt_candidates:
                    selected_txt = txt_candidates[-1]

            if selected_txt is None:
                continue

            content = self._read_text(selected_txt)
            if not content:
                continue

            consumed_txt_paths.add(selected_txt.resolve())
            relative_path = selected_txt.relative_to(policies_root)
            authority = relative_path.parts[0] if len(relative_path.parts) > 1 else "Unknown"
            policy_dir_name = policy_dir.name
            policy_title = policy_dir_name.replace("_", " ").strip().title() or selected_txt.stem
            policy_id = f"{authority.lower()}-{policy_dir_name.lower()}"
            effective_date = str(metadata_raw.get("last_processed_date", "")).split("T")[0]

            metadatas.append(
                {
                    "policy_id": policy_id,
                    "policy_name": policy_title,
                    "authority": authority,
                    "version": selected_txt.stem,
                    "effective_date": effective_date,
                    "processing_status": self._normalize_processing_status(metadata_raw.get("processing_status")),
                }
            )
            documents.append(content)

        for txt_path in sorted(policies_root.rglob("*.txt")):
            if txt_path.resolve() in consumed_txt_paths:
                continue

            content = self._read_text(txt_path)
            if not content:
                continue

            relative_path = txt_path.relative_to(policies_root)
            authority = relative_path.parts[0] if len(relative_path.parts) > 1 else "Unknown"
            policy_id = f"{authority.lower()}-{txt_path.stem.lower()}"
            metadatas.append(
                {
                    "policy_id": policy_id,
                    "policy_name": txt_path.stem.replace("_", " ").strip().title(),
                    "authority": authority,
                    "version": txt_path.stem,
                    "effective_date": "",
                    "processing_status": "Processed",
                }
            )
            documents.append(content)

        return VectorDocumentsResponse(documents=documents, metadatas=metadatas)

    def _read_json(self, path: Path) -> dict[str, object]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
            return {}
        except Exception:
            logger.warning("unable_to_read_metadata_file", extra={"extra": {"path": str(path)}})
            return {}

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").strip()
        except Exception:
            logger.warning("unable_to_read_policy_text", extra={"extra": {"path": str(path)}})
            return ""

    def _normalize_processing_status(self, value: object) -> str:
        if value is None:
            return "Processed"
        lowered = str(value).strip().lower()
        if lowered in {"processed", "complete", "completed", "success"}:
            return "Processed"
        if lowered in {"pending", "queued", "in_progress", "in-progress"}:
            return "Pending"
        return "Processed"


def validate_storage_dependencies() -> None:
    if not Path(config.policies_path).exists():
        raise DependencyError("Policies path is missing", code="POLICIES_PATH_MISSING")
