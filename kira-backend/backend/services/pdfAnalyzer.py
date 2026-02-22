import asyncio
import json
import math
import re
from pathlib import Path
from typing import Any

from backend.core.config import config
from backend.core.llm_client import LlmClient


ANALYSIS_PROMPT_TEMPLATE = """You are an Indian Regulatory Intelligence Engine.

Analyze the following official Gazette notification.

Extract:

1. Regulation name
2. Ministry/Department
3. Policy type (Act, Amendment, Notification, Circular, Rule)
4. Date of issue
5. Effective date
6. Industries impacted
7. Departments impacted (HR, Legal, Finance, IT, Operations)
8. Compliance actions required
9. Penalties for non-compliance
10. Risk level (Low, Medium, High)

Rules:
- Do not hallucinate.
- If a field is unclear, return null.
- Only use the provided text.
- Return strictly valid JSON.

Return JSON using this exact schema:
{
  "policy_name": "",
  "ministry": "",
  "policy_type": "",
  "date_of_issue": "",
  "effective_date": "",
  "industries_impacted": [],
  "departments_impacted": [],
  "compliance_actions_required": [],
  "penalties": "",
  "risk_level": ""
}

Gazette Subject: {subject}
Gazette ID: {gazette_id}
Gazette Text:
{gazette_text}
"""


class PdfAnalyzerService:
    def __init__(self, llm_client: LlmClient) -> None:
        self.llm_client = llm_client

    @staticmethod
    def _candidate_paths() -> list[Path]:
        cwd = Path.cwd()
        project_root = Path(__file__).resolve().parents[2]
        data_file = "Gazetted_data_18-02-2026.json"

        return [
            Path(config.policies_path) / data_file,
            Path("backend/data/policies") / data_file,
            project_root / "backend" / "data" / "policies" / data_file,
            cwd / "backend" / "data" / "policies" / data_file,
            cwd / data_file,
        ]

    def _load_gazettes(self) -> list[dict[str, Any]]:
        path: Path | None = None
        for candidate in self._candidate_paths():
            if candidate.exists() and candidate.is_file():
                path = candidate
                break

        if path is None:
            return []

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return []

        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, math.ceil(len(text) / 4))

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 12000, overlap: int = 800) -> list[str]:
        if len(text) <= max_chars:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = max(end - overlap, 0)
        return chunks

    async def _semantic_top_chunks(self, text: str, query: str, k: int = 3) -> list[str]:
        chunks = self._chunk_text(text)
        if len(chunks) <= k:
            return chunks

        try:
            query_embedding = await self.llm_client.generate_embedding(query)
            scored: list[tuple[float, str]] = []
            query_norm = math.sqrt(sum(v * v for v in query_embedding)) or 1.0

            for chunk in chunks:
                chunk_embedding = await self.llm_client.generate_embedding(chunk[:6000])
                chunk_norm = math.sqrt(sum(v * v for v in chunk_embedding)) or 1.0
                dot = sum(a * b for a, b in zip(query_embedding, chunk_embedding))
                score = dot / (query_norm * chunk_norm)
                scored.append((score, chunk))

            scored.sort(key=lambda item: item[0], reverse=True)
            return [chunk for _, chunk in scored[:k]]
        except Exception:
            return chunks[:k]

    async def _call_json_with_single_retry(self, prompt: str) -> dict[str, Any] | None:
        for attempt in range(2):
            try:
                payload = await self.llm_client.generate_json(prompt)
                if isinstance(payload, dict):
                    return payload
            except Exception:
                if attempt == 1:
                    return None
        return None

    @staticmethod
    def _normalize_analysis(payload: dict[str, Any]) -> dict[str, Any]:
        def list_or_empty(value: Any) -> list[str]:
            if isinstance(value, list):
                return [str(item) for item in value if str(item).strip()]
            return []

        return {
            "policy_name": str(payload.get("policy_name") or "").strip() or None,
            "ministry": str(payload.get("ministry") or "").strip() or None,
            "policy_type": str(payload.get("policy_type") or "").strip() or None,
            "date_of_issue": str(payload.get("date_of_issue") or "").strip() or None,
            "effective_date": str(payload.get("effective_date") or "").strip() or None,
            "industries_impacted": list_or_empty(payload.get("industries_impacted")),
            "departments_impacted": list_or_empty(payload.get("departments_impacted")),
            "compliance_actions_required": list_or_empty(payload.get("compliance_actions_required")),
            "penalties": str(payload.get("penalties") or "").strip() or None,
            "risk_level": str(payload.get("risk_level") or "").strip() or None,
        }

    async def analyze_gazette(self, gazette_id: str) -> dict[str, Any]:
        gazettes = await asyncio.to_thread(self._load_gazettes)
        record = next((row for row in gazettes if str(row.get("id", "")).strip() == gazette_id.strip()), None)
        if record is None:
            return {"error": "Policy analysis temporarily unavailable"}

        text = str(record.get("text") or "").strip()
        subject = str(record.get("subject") or "").strip()
        url = str(record.get("url") or "").strip()
        if not text:
            return {
                "gazette_id": gazette_id,
                "subject": subject or None,
                "url": url or None,
                "analysis": None,
                "fallback_text": "",
            }

        analysis_text = text
        if self._estimate_tokens(text) > 10000:
            chunks = await self._semantic_top_chunks(
                text,
                "regulation name ministry policy type date effective date industry departments compliance penalties risk",
                k=3,
            )
            analysis_text = "\n\n---\n\n".join(chunks)

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(subject=subject, gazette_id=gazette_id, gazette_text=analysis_text)
        payload = await self._call_json_with_single_retry(prompt)

        if payload is None:
            return {
                "error": "Policy analysis temporarily unavailable",
                "gazette_id": gazette_id,
                "subject": subject or None,
                "url": url or None,
                "fallback_text": text[:1200],
            }

        return {
            "gazette_id": gazette_id,
            "subject": subject or None,
            "url": url or None,
            "analysis": self._normalize_analysis(payload),
            "fallback_text": text[:1200],
        }

    async def analyze_all(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = (await asyncio.to_thread(self._load_gazettes))[: max(limit, 1)]
        results: list[dict[str, Any]] = []
        for row in rows:
            gazette_id = str(row.get("id") or "").strip()
            if not gazette_id:
                continue
            result = await self.analyze_gazette(gazette_id)
            if "error" in result and not result.get("fallback_text"):
                result["fallback_text"] = str(row.get("text") or "")[:1200]
            if not result.get("subject"):
                result["subject"] = str(row.get("subject") or "").strip() or None
            if not result.get("url"):
                result["url"] = str(row.get("url") or "").strip() or None
            results.append(result)
        return results

    @staticmethod
    def _tokenize(value: str) -> list[str]:
        return re.findall(r"[a-zA-Z]{3,}", value.lower())

    def get_record(self, gazette_id: str) -> dict[str, Any] | None:
        gazettes = self._load_gazettes()
        return next((row for row in gazettes if str(row.get("id", "")).strip() == gazette_id.strip()), None)
