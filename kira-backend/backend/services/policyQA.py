import asyncio
import math
import re
from typing import Any

from backend.core.llm_client import LlmClient
from backend.services.pdfAnalyzer import PdfAnalyzerService


NOT_FOUND_MESSAGE = "No verified information found in available gazette records."


class PolicyQAService:
    def __init__(self, llm_client: LlmClient, analyzer: PdfAnalyzerService) -> None:
        self.llm_client = llm_client
        self.analyzer = analyzer

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 3500, overlap: int = 300) -> list[str]:
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

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-zA-Z]{3,}", value.lower())}

    async def _rank_chunks(self, question: str, records: list[dict[str, Any]]) -> list[dict[str, str]]:
        query_tokens = self._tokenize(question)
        candidates: list[dict[str, Any]] = []

        for record in records:
            gazette_id = str(record.get("id") or "").strip()
            text = str(record.get("text") or "").strip()
            if not gazette_id or not text:
                continue

            chunks = self._chunk_text(text)
            for chunk in chunks:
                chunk_tokens = self._tokenize(chunk)
                lexical_score = 0.0
                if query_tokens:
                    lexical_score = len(query_tokens.intersection(chunk_tokens)) / len(query_tokens)
                if lexical_score > 0:
                    candidates.append(
                        {
                            "gazette_id": gazette_id,
                            "subject": str(record.get("subject") or "").strip(),
                            "chunk": chunk,
                            "score": lexical_score,
                        }
                    )

        if not candidates:
            return []

        candidates.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
        narrowed = candidates[:12]

        try:
            query_embedding = await self.llm_client.generate_embedding(question)
            query_norm = math.sqrt(sum(v * v for v in query_embedding)) or 1.0

            rescored: list[dict[str, Any]] = []
            for item in narrowed:
                chunk_embedding = await self.llm_client.generate_embedding(str(item["chunk"])[:6000])
                chunk_norm = math.sqrt(sum(v * v for v in chunk_embedding)) or 1.0
                dot = sum(a * b for a, b in zip(query_embedding, chunk_embedding))
                similarity = dot / (query_norm * chunk_norm)
                blended = (float(item["score"]) * 0.4) + (similarity * 0.6)
                item["score"] = blended
                rescored.append(item)

            rescored.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
            top = rescored[:3]
        except Exception:
            top = narrowed[:3]

        return [
            {
                "gazette_id": str(item["gazette_id"]),
                "subject": str(item["subject"]),
                "chunk": str(item["chunk"]),
            }
            for item in top
        ]

    async def _call_with_single_retry(self, prompt: str) -> str | None:
        for attempt in range(2):
            try:
                output = await self.llm_client.generate_text(prompt)
                cleaned = output.strip()
                if cleaned:
                    return cleaned
            except Exception:
                if attempt == 1:
                    return None
        return None

    async def ask(self, question: str, gazette_id: str | None = None) -> dict[str, Any]:
        records = await asyncio.to_thread(self.analyzer._load_gazettes)
        if gazette_id:
            records = [row for row in records if str(row.get("id") or "").strip() == gazette_id.strip()]

        if not records:
            return {"answer": NOT_FOUND_MESSAGE, "sources": []}

        chunks = await self._rank_chunks(question, records)
        if not chunks:
            return {"answer": NOT_FOUND_MESSAGE, "sources": []}

        excerpt_text = "\n\n".join(
            [
                f"[Gazette ID: {item['gazette_id']}; Subject: {item['subject']}]\n{item['chunk']}"
                for item in chunks
            ]
        )

        prompt = (
            "You are a compliance assistant.\n\n"
            "Answer the user's question strictly using the provided gazette excerpts.\n\n"
            "If the answer is not clearly found in the excerpts, say:\n"
            f'"{NOT_FOUND_MESSAGE}"\n\n'
            "Do not fabricate information.\n"
            "Do not use external knowledge.\n"
            "Keep answer concise.\n\n"
            f"Question: {question}\n\n"
            f"Gazette Excerpts:\n{excerpt_text}"
        )

        answer = await self._call_with_single_retry(prompt)
        if answer is None:
            return {"error": "Policy analysis temporarily unavailable", "sources": chunks}

        if NOT_FOUND_MESSAGE.lower() in answer.lower():
            return {"answer": NOT_FOUND_MESSAGE, "sources": chunks}

        return {"answer": answer, "sources": chunks}
